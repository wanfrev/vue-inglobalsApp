import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from openai import APIConnectionError, APIStatusError

from app.config import settings
from app.core.engine import MODEL_LABELS, run_finalize, run_phase1, run_simulation
from app.core.rag import extract_attachment_text
from app.core.session import get_current_session
from app.database import get_draft, increment_free_queries, insert_draft
from app.models.schemas import Loop1Result, SimulateResponse, UsageInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["simulate"])

# Mismos formatos que la bibliografía compartida (ver app/api/documents.py) —
# reutiliza extract_attachment_text(), que reutiliza load_document_text().
ALLOWED_ATTACHMENT_EXTENSIONS = (".pdf", ".docx", ".txt")

FINALIZE_MODES = ("seguir", "complementar", "modelo")


def _read_attachment(file: UploadFile | None, max_chars: int | None = None) -> tuple[str, str]:
    """Valida y extrae el texto de un archivo adjunto opcional. Devuelve
    (texto, nombre_de_archivo); ("", "") si no hay archivo."""
    if file is None:
        return "", ""
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
        text = extract_attachment_text(file.filename, content, max_chars=max_chars)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return text, file.filename


def _run_guarded(fn, *args, **kwargs):
    """Ejecuta un paso del motor traduciendo los errores a respuestas HTTP. El
    detalle real del error (cuotas, IDs de proyecto, URLs internas del
    proveedor) va solo al log del servidor — al usuario le llega un mensaje
    genérico."""
    try:
        return fn(*args, **kwargs)
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


def _finish(result: dict, session: dict, count_query: bool) -> dict:
    """Sin límite de consultas. Se sigue contando "free_queries_used" por
    sesión solo a modo informativo/estadístico — ya no bloquea nada (ver
    config.py). Una pregunta fuera de contexto no suma al contador (el
    organizador la cortó antes de llegar al veredicto)."""
    used = session["free_queries_used"]
    if count_query:
        increment_free_queries(session["token"])
        used += 1
    result["free_queries_used"] = used
    result["is_paid"] = bool(session["is_paid"])
    return result


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
    """Flujo completo en un solo paso (reformulación + Loop 1 + Loop 2). La
    interfaz usa /simulate/start + /simulate/finalize; este queda como camino
    directo."""
    # Rutas síncronas a propósito (no "async def"): el motor es 100%
    # bloqueante (llamadas HTTP al proveedor de IA + fetch de las webs en
    # vivo, sin ningún await). Con "async def", esas esperas (varios
    # segundos) congelarían el event loop y bloquearían a TODOS los usuarios
    # concurrentes. Con "def", FastAPI las corre en un threadpool.
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    attached_text, attached_filename = _read_attachment(file)
    result = _run_guarded(
        run_simulation,
        session_token=session["token"],
        prompt=prompt,
        attached_text=attached_text,
        attached_filename=attached_filename,
    )
    return _finish(result, session, count_query=result.get("in_scope") is not False)


@router.post("/simulate/start", response_model=SimulateResponse)
def simulate_start(
    prompt: str = Form(...),
    file: UploadFile | None = File(None),
    session: dict = Depends(get_current_session),
):
    """Paso 1: reformulación + Loop 1. Devuelve lo que la bibliografía permitió
    verificar y un `draft_id`; el usuario decide entonces cómo seguir
    (/simulate/finalize). No cuenta como consulta ni crea expediente todavía."""
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    attached_text, attached_filename = _read_attachment(file)
    phase1 = _run_guarded(run_phase1, prompt, attached_text=attached_text, attached_filename=attached_filename)

    if phase1.get("in_scope") is False:
        return _finish(phase1, session, count_query=False)

    draft = phase1["draft"]
    draft_id = uuid.uuid4().hex
    insert_draft(draft_id, session["token"], draft)

    loop1 = Loop1Result(**draft["loop1"])
    usage = UsageInfo(**draft["usage_0"]).model_dump()
    for k, v in draft["usage_1"].items():
        usage[k] = usage.get(k, 0) + v
    response = {
        "in_scope": True,
        "draft_id": draft_id,
        "refined_question": draft["refined_question"],
        "attached_filename": draft["attached_filename"],
        "entity_type": loop1.entity_type,
        "framework": loop1.framework,
        "missing_info": loop1.missing_info,
        "sources_used": draft["sources_used"],
        "loop1": loop1.model_dump(),
        "model_kind": draft["model_kind"],
        "usage": usage,
    }
    return _finish(response, session, count_query=False)


@router.post("/simulate/finalize", response_model=SimulateResponse)
def simulate_finalize(
    draft_id: str = Form(...),
    # "seguir": respuesta final con lo verificado en la bibliografía.
    # "complementar": antes, búsqueda externa con el modelo de IA (marcada
    #   como no verificada) para cubrir lo que falta.
    # "modelo": genera un modelo (plan de cuentas / estados financieros).
    mode: str = Form("seguir"),
    kind: str = Form(""),
    # Solo para mode="modelo": documento anterior que se quiere actualizar.
    file: UploadFile | None = File(None),
    session: dict = Depends(get_current_session),
):
    """Paso 2: retoma el borrador según la decisión del usuario."""
    if mode not in FINALIZE_MODES:
        raise HTTPException(status_code=400, detail="Opción no válida.")
    if mode == "modelo" and kind and kind not in MODEL_LABELS:
        raise HTTPException(status_code=400, detail="Tipo de modelo no válido.")

    draft = get_draft(draft_id, session["token"])
    if not draft:
        raise HTTPException(
            status_code=404,
            detail="Esta consulta ya no está disponible (venció o no es de tu sesión). Vuelve a enviarla.",
        )

    old_text, old_name = ("", "")
    if mode == "modelo":
        old_text, old_name = _read_attachment(file, max_chars=settings.MODEL_ATTACHMENT_MAX_CHARS)

    result = _run_guarded(
        run_finalize,
        session["token"],
        draft,
        mode=mode,
        model_kind=kind,
        model_old_text=old_text,
        model_old_name=old_name,
    )
    return _finish(result, session, count_query=True)
