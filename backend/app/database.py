import json
import os
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings

_embedding_model = None
_faiss_index = None
_faiss_metadata: list[dict] = []


def get_sqlite_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.SQLITE_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_sqlite() -> None:
    conn = get_sqlite_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anon_sessions (
            token TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            free_queries_used INTEGER NOT NULL DEFAULT 0,
            is_paid INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT REFERENCES anon_sessions(token),
            expediente_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            framework TEXT NOT NULL,
            prompt TEXT NOT NULL,
            structured_prompt TEXT NOT NULL DEFAULT '',
            result_json TEXT,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            estimated_cost_usd REAL NOT NULL DEFAULT 0,
            energy_wh REAL NOT NULL DEFAULT 0,
            co2_g REAL NOT NULL DEFAULT 0
        )
    """)

    # CREATE TABLE IF NOT EXISTS no altera una tabla que ya existe: una base
    # creada con el esquema anterior (la ecuación DAD, con columnas
    # criteria_*/compliance_score que ya no se usan pero siguen ahí con sus
    # DEFAULT, así que los INSERT nuevos que las omiten funcionan) no tendría
    # las columnas de energía. Se agregan aquí si faltan.
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(simulations)")}
    for column in ("energy_wh", "co2_g"):
        if column not in existing_columns:
            conn.execute(f"ALTER TABLE simulations ADD COLUMN {column} REAL NOT NULL DEFAULT 0")

    # Borradores del flujo en dos pasos: tras el Loop 1 el usuario decide cómo
    # seguir (respuesta final, búsqueda externa, generar un modelo...) y el
    # servidor retoma desde aquí — así el cliente no puede alterar lo que el
    # Loop 1 "verificó".
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulation_drafts (
            id TEXT PRIMARY KEY,
            session_token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


# Con Gunicorn corriendo varios workers, cada uno tiene su propia copia del
# índice en memoria. Dos problemas reales que ya vimos en producción:
#  1. Un worker "frío" devolvía una lista vacía aunque el índice existiera en
#     disco (dependía de a qué worker te tocara).
#  2. "Lost update": cada worker guardaba SU copia completa, así que al subir
#     varios documentos seguidos (repartidos entre workers) el último en
#     guardar pisaba lo que había agregado el otro — se perdieron 6 de 12
#     documentos subidos. Por eso: (a) todo cambio al índice se hace bajo un
#     candado entre procesos, recargando antes desde disco lo que otro worker
#     haya guardado, y (b) cada worker detecta (por el archivo de metadatos,
#     que se escribe al final) que el disco cambió y recarga.
try:
    import fcntl
except ImportError:  # Windows (solo desarrollo local, un solo proceso)
    fcntl = None

_thread_lock = threading.RLock()
_lock_depth = 0
_lock_file = None
_loaded_stamp = None


@contextmanager
def faiss_write_lock():
    """Candado exclusivo entre procesos (y threads) para modificar el índice.
    Reentrante dentro del mismo thread."""
    global _lock_depth, _lock_file
    with _thread_lock:
        if _lock_depth == 0 and fcntl is not None:
            _lock_file = open(settings.CHROMA_DIR / "faiss.lock", "a+")
            fcntl.flock(_lock_file, fcntl.LOCK_EX)
        _lock_depth += 1
        try:
            yield
        finally:
            _lock_depth -= 1
            if _lock_depth == 0 and _lock_file is not None:
                fcntl.flock(_lock_file, fcntl.LOCK_UN)
                _lock_file.close()
                _lock_file = None


def _meta_stamp():
    try:
        st = (settings.CHROMA_DIR / "faiss_metadata.json").stat()
        return (st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        return None


def refresh_faiss_from_disk(dimension: int = 384) -> None:
    """Descarta la copia en memoria y vuelve a leer el índice y los metadatos
    desde disco. Llamar siempre dentro de faiss_write_lock() antes de
    modificar el índice."""
    global _faiss_index, _faiss_metadata, _loaded_stamp
    import faiss
    with faiss_write_lock():
        index_path = settings.CHROMA_DIR / "faiss.index"
        meta_path = settings.CHROMA_DIR / "faiss_metadata.json"
        stamp = _meta_stamp()
        if index_path.exists() and stamp is not None:
            new_index = faiss.read_index(str(index_path))
            with open(meta_path, "r", encoding="utf-8") as f:
                new_metadata = json.load(f)
            _faiss_index = new_index
            _faiss_metadata = new_metadata
        else:
            _faiss_index = faiss.IndexFlatIP(dimension)
            _faiss_metadata = []
        _loaded_stamp = stamp


def _ensure_faiss_loaded(dimension: int = 384) -> None:
    """Carga el índice desde disco si este worker aún no lo ha hecho, o si
    otro worker lo modificó desde la última carga."""
    if _faiss_index is None or _meta_stamp() != _loaded_stamp:
        refresh_faiss_from_disk(dimension)


def get_faiss_index(dimension: int = 384):
    _ensure_faiss_loaded(dimension)
    return _faiss_index


def save_faiss_index() -> None:
    """Escribe el índice y los metadatos a disco de forma atómica (archivo
    temporal + reemplazo; los metadatos van al final porque su fecha es la
    señal que usan los demás workers para saber que hay algo nuevo). Llamar
    dentro de faiss_write_lock()."""
    import faiss
    global _loaded_stamp
    if _faiss_index is None:
        return
    with faiss_write_lock():
        index_path = settings.CHROMA_DIR / "faiss.index"
        meta_path = settings.CHROMA_DIR / "faiss_metadata.json"
        tmp_index = index_path.with_suffix(".index.tmp")
        tmp_meta = meta_path.with_suffix(".json.tmp")
        faiss.write_index(_faiss_index, str(tmp_index))
        with open(tmp_meta, "w", encoding="utf-8") as f:
            json.dump(_faiss_metadata, f, ensure_ascii=False)
        os.replace(tmp_index, index_path)
        os.replace(tmp_meta, meta_path)
        _loaded_stamp = _meta_stamp()


def get_metadata() -> list[dict]:
    _ensure_faiss_loaded()
    return _faiss_metadata


# ---------------------------------------------------------------------------
# Sesiones anónimas — sin registro ni login. El cliente pidió quitar el login
# por ahora: cualquiera entra directo, el navegador guarda un token de sesión
# (ver app/core/session.py) y el límite de consultas gratis se cuenta contra
# ESE token, no contra una identidad real. Se pierde/reinicia si el usuario
# borra el almacenamiento local del navegador o usa modo incógnito.
# ---------------------------------------------------------------------------

def create_anon_session() -> dict:
    token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(days=settings.SESSION_EXPIRY_DAYS)
    conn = get_sqlite_connection()
    conn.execute(
        "INSERT INTO anon_sessions (token, created_at, expires_at) VALUES (?, ?, ?)",
        (token, created_at.isoformat(), expires_at.isoformat()),
    )
    conn.commit()
    conn.close()
    return {
        "token": token,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "free_queries_used": 0,
        "is_paid": 0,
    }


def get_session_by_token(token: str) -> dict | None:
    conn = get_sqlite_connection()
    row = conn.execute(
        "SELECT * FROM anon_sessions WHERE token = ? AND expires_at > ?",
        (token, datetime.now(timezone.utc).isoformat()),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def increment_free_queries(token: str) -> None:
    conn = get_sqlite_connection()
    conn.execute(
        "UPDATE anon_sessions SET free_queries_used = free_queries_used + 1 WHERE token = ?",
        (token,),
    )
    conn.commit()
    conn.close()


def set_session_paid(token: str, is_paid: bool = True) -> None:
    """Marca una sesión como paga. Hoy no hay pasarela de pago conectada —
    esto se llama manualmente (o desde el flujo que se integre después) tras
    confirmar el pago."""
    conn = get_sqlite_connection()
    conn.execute("UPDATE anon_sessions SET is_paid = ? WHERE token = ?", (1 if is_paid else 0, token))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Simulaciones
# ---------------------------------------------------------------------------

def get_simulations(
    session_token: str,
    entity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    conn = get_sqlite_connection()
    query = "SELECT * FROM simulations WHERE session_token = ?"
    params: list = [session_token]

    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.append(limit)
    params.append(offset)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_today_cost_usd() -> float:
    """Suma el costo estimado de todas las simulaciones creadas desde la
    medianoche UTC de hoy — usado para la alerta de gasto diario (ver
    app/core/engine.py)."""
    start_of_day = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    conn = get_sqlite_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(estimated_cost_usd), 0) AS total FROM simulations WHERE created_at >= ?",
        (start_of_day,),
    ).fetchone()
    conn.close()
    return float(row["total"])


def get_simulation_by_expediente(expediente_id: str, session_token: str) -> dict | None:
    conn = get_sqlite_connection()
    row = conn.execute(
        "SELECT * FROM simulations WHERE expediente_id = ? AND session_token = ?",
        (expediente_id, session_token),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_draft(draft_id: str, session_token: str, payload: dict) -> None:
    conn = get_sqlite_connection()
    # Los borradores sin usar no se acumulan para siempre.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    conn.execute("DELETE FROM simulation_drafts WHERE created_at < ?", (cutoff,))
    conn.execute(
        "INSERT INTO simulation_drafts (id, session_token, created_at, payload_json) VALUES (?, ?, ?, ?)",
        (draft_id, session_token, datetime.now(timezone.utc).isoformat(), json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def get_draft(draft_id: str, session_token: str) -> dict | None:
    conn = get_sqlite_connection()
    row = conn.execute(
        "SELECT payload_json FROM simulation_drafts WHERE id = ? AND session_token = ?",
        (draft_id, session_token),
    ).fetchone()
    conn.close()
    return json.loads(row["payload_json"]) if row else None


def insert_simulation(data: dict) -> int:
    conn = get_sqlite_connection()
    cursor = conn.execute(
        """
        INSERT INTO simulations (
            session_token, expediente_id, created_at, entity_type, framework, prompt,
            structured_prompt, result_json, prompt_tokens, completion_tokens,
            total_tokens, estimated_cost_usd, energy_wh, co2_g
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data["session_token"],
            data["expediente_id"],
            data["created_at"],
            data["entity_type"],
            data["framework"],
            data["prompt"],
            data.get("structured_prompt", ""),
            data.get("result_json", ""),
            data.get("prompt_tokens", 0),
            data.get("completion_tokens", 0),
            data.get("total_tokens", 0),
            data.get("estimated_cost_usd", 0),
            data.get("energy_wh", 0),
            data.get("co2_g", 0),
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id
