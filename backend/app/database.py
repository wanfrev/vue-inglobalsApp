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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            free_queries_used INTEGER NOT NULL DEFAULT 0,
            is_paid INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            expediente_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            framework TEXT NOT NULL,
            prompt TEXT NOT NULL,
            structured_prompt TEXT NOT NULL DEFAULT '',
            attached_files TEXT NOT NULL DEFAULT '[]',
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
# Usuarios y sesiones (registro rápido por correo, sin verificación de email
# todavía — ver app/core/auth.py para el hashing y la resolución de token).
# ---------------------------------------------------------------------------

def create_user(email: str, password_hash: str) -> dict:
    conn = get_sqlite_connection()
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, created_at),
        )
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()
    return {
        "id": user_id,
        "email": email,
        "created_at": created_at,
        "free_queries_used": 0,
        "is_paid": 0,
    }


def get_user_by_email(email: str) -> dict | None:
    conn = get_sqlite_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_sqlite_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def increment_free_queries(user_id: int) -> None:
    conn = get_sqlite_connection()
    conn.execute(
        "UPDATE users SET free_queries_used = free_queries_used + 1 WHERE id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()


def set_user_paid(user_id: int, is_paid: bool = True) -> None:
    """Marca una cuenta como paga. Hoy no hay pasarela de pago conectada —
    esto se llama manualmente (o desde el flujo que se integre después) tras
    confirmar el pago."""
    conn = get_sqlite_connection()
    conn.execute("UPDATE users SET is_paid = ? WHERE id = ?", (1 if is_paid else 0, user_id))
    conn.commit()
    conn.close()


def create_session(user_id: int) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(days=settings.SESSION_EXPIRY_DAYS)
    conn = get_sqlite_connection()
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, created_at.isoformat(), expires_at.isoformat()),
    )
    conn.commit()
    conn.close()
    return token, expires_at.isoformat()


def get_user_by_token(token: str) -> dict | None:
    conn = get_sqlite_connection()
    row = conn.execute(
        """
        SELECT users.* FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ? AND sessions.expires_at > ?
        """,
        (token, datetime.now(timezone.utc).isoformat()),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(token: str) -> None:
    conn = get_sqlite_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Simulaciones
# ---------------------------------------------------------------------------

def _decode_row(row: dict) -> dict:
    try:
        row["attached_files"] = json.loads(row.get("attached_files") or "[]")
    except (TypeError, ValueError):
        row["attached_files"] = []
    return row


def get_simulations(
    user_id: int,
    entity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    conn = get_sqlite_connection()
    query = "SELECT * FROM simulations WHERE user_id = ?"
    params: list = [user_id]

    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.append(limit)
    params.append(offset)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_decode_row(dict(row)) for row in rows]


def get_simulation_by_expediente(expediente_id: str, user_id: int) -> dict | None:
    conn = get_sqlite_connection()
    row = conn.execute(
        "SELECT * FROM simulations WHERE expediente_id = ? AND user_id = ?",
        (expediente_id, user_id),
    ).fetchone()
    conn.close()
    return _decode_row(dict(row)) if row else None


def insert_simulation(data: dict) -> int:
    conn = get_sqlite_connection()
    cursor = conn.execute(
        """
        INSERT INTO simulations (
            user_id, expediente_id, created_at, entity_type, framework, prompt,
            structured_prompt, attached_files, result_json, is_valid, criteria_cs, criteria_cv,
            criteria_cs_cap, criteria_gt, criteria_ni, compliance_score,
            corrective_action, question_well_formed, question_feedback,
            prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data["user_id"],
            data["expediente_id"],
            data["created_at"],
            data["entity_type"],
            data["framework"],
            data["prompt"],
            data.get("structured_prompt", ""),
            data.get("attached_files", "[]"),
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
