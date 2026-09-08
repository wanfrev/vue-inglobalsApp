from fastapi import APIRouter, Form, HTTPException, UploadFile, File

from app.core.attachments import MAX_ATTACHMENTS_PER_REQUEST, extract_text
from app.core.engine import run_simulation
from app.models.schemas import SimulateResponse

router = APIRouter(prefix="/api/v1", tags=["simulate"])


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(
    prompt: str = Form(...),
    files: list[UploadFile] = File(default=[]),
):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

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
        result = run_simulation(prompt=prompt, attachments=attachments)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")
