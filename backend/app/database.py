import json
import secrets
import sqlite3
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
            is_valid INTEGER NOT NULL DEFAULT 0,
            criteria_cs TEXT NOT NULL DEFAULT 'idle',
            criteria_cv TEXT NOT NULL DEFAULT 'idle',
            criteria_cs_cap TEXT NOT NULL DEFAULT 'idle',
            criteria_gt TEXT NOT NULL DEFAULT 'idle',
            criteria_ni TEXT NOT NULL DEFAULT 'idle',
            compliance_score INTEGER NOT NULL DEFAULT 0,
            corrective_action TEXT NOT NULL DEFAULT '',
            question_well_formed INTEGER NOT NULL DEFAULT 1,
            question_feedback TEXT NOT NULL DEFAULT '',
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            estimated_cost_usd REAL NOT NULL DEFAULT 0
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


def get_faiss_index(dimension: int = 384):
    global _faiss_index
    if _faiss_index is None:
        import faiss
        index_path = settings.CHROMA_DIR / "faiss.index"
        meta_path = settings.CHROMA_DIR / "faiss_metadata.json"
        if index_path.exists():
            _faiss_index = faiss.read_index(str(index_path))
            with open(meta_path, "r", encoding="utf-8") as f:
                _faiss_metadata.extend(json.load(f))
        else:
            _faiss_index = faiss.IndexFlatIP(dimension)
    return _faiss_index


def save_faiss_index() -> None:
    import faiss
    global _faiss_index
    if _faiss_index is not None:
        index_path = settings.CHROMA_DIR / "faiss.index"
        meta_path = settings.CHROMA_DIR / "faiss_metadata.json"
        faiss.write_index(_faiss_index, str(index_path))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(_faiss_metadata, f, ensure_ascii=False, indent=2)


def get_metadata() -> list[dict]:
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


def insert_simulation(data: dict) -> int:
    conn = get_sqlite_connection()
    cursor = conn.execute(
        """
        INSERT INTO simulations (
            session_token, expediente_id, created_at, entity_type, framework, prompt,
            structured_prompt, result_json, is_valid, criteria_cs, criteria_cv,
            criteria_cs_cap, criteria_gt, criteria_ni, compliance_score,
            corrective_action, question_well_formed, question_feedback,
            prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            data.get("is_valid", 0),
            data.get("criteria_cs", "idle"),
            data.get("criteria_cv", "idle"),
            data.get("criteria_cs_cap", "idle"),
            data.get("criteria_gt", "idle"),
            data.get("criteria_ni", "idle"),
            data.get("compliance_score", 0),
            data.get("corrective_action", ""),
            data.get("question_well_formed", 1),
            data.get("question_feedback", ""),
            data.get("prompt_tokens", 0),
            data.get("completion_tokens", 0),
            data.get("total_tokens", 0),
            data.get("estimated_cost_usd", 0),
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id
