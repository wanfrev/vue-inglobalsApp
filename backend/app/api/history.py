import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.originals import safe_download_name
from app.core.pdf import build_answer_pdf, build_document_pdf
from app.core.session import get_current_session
from app.database import get_simulation_by_expediente, get_simulations
from app.models.schemas import SimulationRecord

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("", response_model=list[SimulationRecord])
def list_simulations(
    entity_type: str | None = Query(None, description="Filtrar por tipo de entidad"),
    limit: int = Query(50, ge=1, le=200, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    session: dict = Depends(get_current_session),
):
    return get_simulations(session_token=session["token"], entity_type=entity_type, limit=limit, offset=offset)


@router.get("/{expediente_id}", response_model=SimulationRecord)
def get_simulation(expediente_id: str, session: dict = Depends(get_current_session)):
    simulation = get_simulation_by_expediente(expediente_id, session_token=session["token"])
    if not simulation:
        raise HTTPException(
            status_code=404, detail=f"Expediente '{expediente_id}' no encontrado"
        )
    return simulation


@router.get("/{expediente_id}/export")
def export_simulation(expediente_id: str, session: dict = Depends(get_current_session)):
    """Descarga la respuesta en PDF (a pedido del cliente: nunca en JSON). El
    PDF lleva la consulta, la respuesta y la bibliografía consultada; a
    propósito NO incluye la trazabilidad del Loop 1, los prompts ni las
    métricas internas. Si la consulta generó un modelo (plan de cuentas /
    estados financieros), el PDF es ese documento. Libre para cualquier
    sesión, pagada o no."""
    simulation = get_simulation_by_expediente(expediente_id, session_token=session["token"])
    if not simulation:
        raise HTTPException(
            status_code=404, detail=f"Expediente '{expediente_id}' no encontrado"
        )

    try:
        record = json.loads(simulation.get("result_json") or "{}")
    except json.JSONDecodeError:
        record = {}
    record["prompt"] = simulation.get("prompt", "")
    record.setdefault("expediente_id", expediente_id)
    record.setdefault("created_at", simulation.get("created_at", ""))

    model_doc = record.get("model_document")
    if model_doc and model_doc.get("content"):
        pdf = build_document_pdf(
            model_doc.get("title") or "Modelo generado",
            model_doc["content"],
            subtitle=" | ".join(x for x in [
                f"Expediente {expediente_id}",
                f"Basado en el documento adjunto: {model_doc['based_on_attachment']}" if model_doc.get("based_on_attachment") else "",
                model_doc.get("notes", ""),
            ] if x),
            doc_label="Modelo generado",
        )
        filename = safe_download_name(model_doc.get("title"), f"modelo-{expediente_id}")
    else:
        pdf = build_answer_pdf(record)
        filename = f"respuesta-{expediente_id}"

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )
