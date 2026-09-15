from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File

from app.config import settings
from app.core.attachments import MAX_ATTACHMENTS_PER_REQUEST, extract_text
from app.core.auth import get_current_user
from app.core.engine import run_simulation
from app.database import increment_free_queries
from app.models.schemas import SimulateResponse

router = APIRouter(prefix="/api/v1", tags=["simulate"])


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(
    prompt: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    user: dict = Depends(get_current_user),
):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    is_paid = bool(user["is_paid"])
    used = user["free_queries_used"]
    if not is_paid and used >= settings.FREE_QUERY_LIMIT:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Alcanzaste el límite de {settings.FREE_QUERY_LIMIT} consultas gratis. "
                "Activa tu cuenta paga para seguir consultando."
            ),
        )

    if len(files) > MAX_ATTACHMENTS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo {MAX_ATTACHMENTS_PER_REQUEST} archivos adjuntos por consulta",
        )

    attachments = []
    for file in files:
        if not file.filename:
            continue
        content = await file.read()
        try:
            text = extract_text(file.filename, content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        attachments.append({"name": file.filename, "text": text})

    try:
        result = run_simulation(user_id=user["id"], prompt=prompt, attachments=attachments)
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
        increment_free_queries(user["id"])
        used += 1

    result["free_queries_used"] = used
    result["free_queries_remaining"] = 0 if is_paid else max(0, settings.FREE_QUERY_LIMIT - used)
    result["is_paid"] = is_paid
    return result
