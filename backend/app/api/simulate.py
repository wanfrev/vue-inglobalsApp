from fastapi import APIRouter, HTTPException

from app.core.engine import run_simulation
from app.models.schemas import SimulateRequest, SimulateResponse

router = APIRouter(prefix="/api/v1", tags=["simulate"])


@router.post("/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest):
    try:
        result = run_simulation(
            prompt=request.prompt,
            entity_type=request.entity_type,
            framework=request.framework,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")
