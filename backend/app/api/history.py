from fastapi import APIRouter, HTTPException, Query

from app.database import get_simulation_by_expediente, get_simulations
from app.models.schemas import SimulationRecord

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("", response_model=list[SimulationRecord])
def list_simulations(
    entity_type: str | None = Query(None, description="Filtrar por tipo de entidad"),
    limit: int = Query(50, ge=1, le=200, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
):
    return get_simulations(entity_type=entity_type, limit=limit, offset=offset)


@router.get("/{expediente_id}", response_model=SimulationRecord)
def get_simulation(expediente_id: str):
    simulation = get_simulation_by_expediente(expediente_id)
    if not simulation:
        raise HTTPException(
            status_code=404, detail=f"Expediente '{expediente_id}' no encontrado"
        )
    return simulation
