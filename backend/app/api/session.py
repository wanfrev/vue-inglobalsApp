from fastapi import APIRouter, Depends

from app.config import settings
from app.core.session import get_current_session
from app.database import create_anon_session
from app.models.schemas import SessionResponse, SessionStatus

router = APIRouter(prefix="/api/v1/session", tags=["session"])


def _remaining(session: dict) -> int:
    if session["is_paid"]:
        return 0
    return max(0, settings.FREE_QUERY_LIMIT - session["free_queries_used"])


@router.post("", response_model=SessionResponse)
def start_session():
    """Crea una sesión anónima nueva — sin correo ni contraseña. El frontend
    llama esto una sola vez (al abrir la app sin un token guardado) y guarda
    el token devuelto para las siguientes peticiones."""
    session = create_anon_session()
    return SessionResponse(
        token=session["token"],
        free_queries_used=session["free_queries_used"],
        free_queries_remaining=_remaining(session),
        is_paid=bool(session["is_paid"]),
    )


@router.get("/me", response_model=SessionStatus)
def me(session: dict = Depends(get_current_session)):
    return SessionStatus(
        free_queries_used=session["free_queries_used"],
        free_queries_remaining=_remaining(session),
        is_paid=bool(session["is_paid"]),
    )
