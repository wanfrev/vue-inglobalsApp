"""Sesiones anónimas por navegador — sin registro ni login. El cliente pidió
quitarlo por ahora: quien entra recibe un token de sesión automático (ver
app/api/session.py) que el frontend guarda en localStorage, y el límite de
consultas gratis se cuenta contra ese token. No hay contraseña que verificar
ni identidad real detrás — es solo un contador por navegador."""

from fastapi import Header, HTTPException

from app.database import get_session_by_token


def get_current_session(authorization: str = Header(default="")) -> dict:
    """Dependency de FastAPI: exige `Authorization: Bearer <token>` y devuelve
    la fila de `anon_sessions` asociada. 401 si falta, es inválido o expiró
    (el frontend debe pedir una sesión nueva en ese caso)."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Falta el token de sesión")

    token = authorization[len("bearer "):].strip()
    session = get_session_by_token(token)
    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    return session
