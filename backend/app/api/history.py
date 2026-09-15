from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.database import get_simulation_by_expediente, get_simulations
from app.models.schemas import SimulationRecord

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("", response_model=list[SimulationRecord])
def list_simulations(
    entity_type: str | None = Query(None, description="Filtrar por tipo de entidad"),
    limit: int = Query(50, ge=1, le=200, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    user: dict = Depends(get_current_user),
):
    return get_simulations(user_id=user["id"], entity_type=entity_type, limit=limit, offset=offset)


@router.get("/{expediente_id}", response_model=SimulationRecord)
def get_simulation(expediente_id: str, user: dict = Depends(get_current_user)):
    simulation = get_simulation_by_expediente(expediente_id, user_id=user["id"])
    if not simulation:
        raise HTTPException(
            status_code=404, detail=f"Expediente '{expediente_id}' no encontrado"
        )
    return simulation


@router.get("/{expediente_id}/export")
def export_simulation(expediente_id: str, user: dict = Depends(get_current_user)):
    if not user["is_paid"]:
        raise HTTPException(
            status_code=402,
            detail="Descargar la memoria técnica requiere una cuenta paga. Activa tu cuenta para continuar.",
        )

    simulation = get_simulation_by_expediente(expediente_id, user_id=user["id"])
    if not simulation:
        raise HTTPException(
            status_code=404, detail=f"Expediente '{expediente_id}' no encontrado"
        )
    return simulation
