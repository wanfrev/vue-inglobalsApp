import logging

from fastapi import APIRouter, Depends, HTTPException
from openai import APIConnectionError, APIStatusError

from app.config import settings
from app.core.session import get_current_session
from app.core.engine import run_simulation
from app.database import increment_free_queries
from app.models.schemas import SimulateRequest, SimulateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["simulate"])


@router.post("/simulate", response_model=SimulateResponse)
def simulate(
    payload: SimulateRequest,
    session: dict = Depends(get_current_session),
):
    # Ruta síncrona a propósito (no "async def"): run_simulation() es 100%
    # bloqueante (llamadas HTTP a Gemini + fetch de las webs en vivo, sin
    # ningún await). Si fuera "async def", esas esperas (varios segundos)
    # congelarían el event loop entero y bloquearían a TODOS los usuarios
    # concurrentes. Con "def" normal, FastAPI la corre en un threadpool y
    # cada request espera solo por sí misma.
    prompt = payload.prompt
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    is_paid = bool(session["is_paid"])
    used = session["free_queries_used"]
    if not is_paid and used >= settings.FREE_QUERY_LIMIT:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Alcanzaste el límite de {settings.FREE_QUERY_LIMIT} consultas gratis. "
                "Activa tu cuenta paga para seguir consultando."
            ),
        )

    # El detalle real del error (cuotas, IDs de proyecto, URLs internas del
    # proveedor) va solo al log del servidor — al usuario le llega un mensaje
    # genérico. Como el contador de consultas gratis solo se descuenta más
    # abajo, cuando run_simulation() terminó bien, un error aquí no le
    # cuesta ninguna consulta al usuario.
    try:
        result = run_simulation(session_token=session["token"], prompt=prompt)
    except (APIStatusError, APIConnectionError) as e:
        logger.error("Proveedores de IA no disponibles para esta consulta: %s", str(e)[:500])
        raise HTTPException(
            status_code=503,
            detail=(
                "El servicio de IA está temporalmente saturado o no disponible. "
                "Intenta de nuevo en unos minutos — no se descontó ninguna consulta gratis."
            ),
        )
    except Exception:
        logger.exception("Error inesperado procesando una simulación")
        raise HTTPException(
            status_code=500,
            detail=(
                "Ocurrió un error procesando tu consulta. "
                "Intenta de nuevo — no se descontó ninguna consulta gratis."
            ),
        )

    # Una pregunta fuera de contexto no consume consultas gratis (el
    # organizador la cortó antes de llegar al veredicto) — ver run_simulation.
    if result.get("in_scope") is False:
        result["free_queries_used"] = used
        result["free_queries_remaining"] = 0 if is_paid else max(0, settings.FREE_QUERY_LIMIT - used)
        result["is_paid"] = is_paid
        return result

    if not is_paid:
        increment_free_queries(session["token"])
        used += 1

    result["free_queries_used"] = used
    result["free_queries_remaining"] = 0 if is_paid else max(0, settings.FREE_QUERY_LIMIT - used)
    result["is_paid"] = is_paid
    return result
