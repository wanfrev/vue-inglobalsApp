from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.core.session import get_current_session
from app.core.engine import run_simulation
from app.database import increment_free_queries
from app.models.schemas import SimulateRequest, SimulateResponse

router = APIRouter(prefix="/api/v1", tags=["simulate"])


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(
    payload: SimulateRequest,
    session: dict = Depends(get_current_session),
):
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

    try:
        result = run_simulation(session_token=session["token"], prompt=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")

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
