import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from openai import APIConnectionError, APIStatusError

from app.config import settings
from app.core.rag import extract_attachment_text
from app.core.session import get_current_session
from app.core.engine import run_simulation
from app.database import increment_free_queries
from app.models.schemas import SimulateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["simulate"])

# Mismos formatos que la bibliografía compartida (ver app/api/documents.py) —
# reutiliza extract_attachment_text(), que reutiliza load_document_text().
ALLOWED_ATTACHMENT_EXTENSIONS = (".pdf", ".docx", ".txt")


@router.post("/simulate", response_model=SimulateResponse)
def simulate(
    prompt: str = Form(...),
    # Archivo opcional adjunto a ESTA consulta puntual (a pedido del
    # cliente) — no se indexa en la bibliografía compartida, es contexto
    # efímero solo para esta consulta (ver run_simulation/_run_loop1 en
    # engine.py). El endpoint pasó de JSON a multipart/form-data por esto;
    # el frontend ya manda FormData siempre (ver services/api.js).
    file: UploadFile | None = File(None),
    session: dict = Depends(get_current_session),
):
    # Ruta síncrona a propósito (no "async def"): run_simulation() es 100%
    # bloqueante (llamadas HTTP a Gemini + fetch de las webs en vivo, sin
    # ningún await). Si fuera "async def", esas esperas (varios segundos)
    # congelarían el event loop entero y bloquearían a TODOS los usuarios
    # concurrentes. Con "def" normal, FastAPI la corre en un threadpool y
    # cada request espera solo por sí misma.
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    is_paid = bool(session["is_paid"])
    used = session["free_queries_used"]

    attached_text = ""
    attached_filename = ""
    if file is not None:
        if not file.filename or not file.filename.lower().endswith(ALLOWED_ATTACHMENT_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail="El adjunto debe ser PDF, Word (.docx) o texto plano (.txt).",
            )
        content = file.file.read()
        max_bytes = settings.ATTACHMENT_MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo adjunto supera el límite de {settings.ATTACHMENT_MAX_FILE_SIZE_MB} MB.",
            )
        try:
            attached_text = extract_attachment_text(file.filename, content)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        attached_filename = file.filename

    # El detalle real del error (cuotas, IDs de proyecto, URLs internas del
    # proveedor) va solo al log del servidor — al usuario le llega un mensaje
    # genérico.
    try:
        result = run_simulation(
            session_token=session["token"],
            prompt=prompt,
            attached_text=attached_text,
            attached_filename=attached_filename,
        )
    except (APIStatusError, APIConnectionError) as e:
        logger.error("Proveedores de IA no disponibles para esta consulta: %s", str(e)[:500])
        raise HTTPException(
            status_code=503,
            detail="El servicio de IA está temporalmente saturado o no disponible. Intenta de nuevo en unos minutos.",
        )
    except Exception:
        logger.exception("Error inesperado procesando una simulación")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error procesando tu consulta. Intenta de nuevo.",
        )

    # Sin límite de consultas. Se sigue contando "free_queries_used" por
    # sesión solo a modo informativo/estadístico — ya no bloquea nada (ver
    # config.py). Una pregunta fuera de contexto no suma al contador (el
    # organizador la cortó antes de llegar al veredicto) — ver run_simulation.
    if result.get("in_scope") is False:
        result["free_queries_used"] = used
        result["is_paid"] = is_paid
        return result

    increment_free_queries(session["token"])
    used += 1

    result["free_queries_used"] = used
    result["is_paid"] = is_paid
    return result
