import mimetypes
import shutil
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.core.admin import require_admin
from app.core.originals import find_original, is_downloadable, safe_download_name, save_original
from app.core.rag import (
    delete_document,
    index_document,
    list_documents,
    search_legal_context,
)
from app.database import get_metadata
from app.models.schemas import DocumentUploadResponse

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

VALID_CATEGORIES = {"venezolana", "internacional", "sostenibilidad", "metodologica"}


@router.post("/upload", response_model=DocumentUploadResponse, dependencies=[Depends(require_admin)])
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: Literal["venezolana", "internacional", "sostenibilidad", "metodologica"] = Form(...),
    date: str = Form(""),
):
    if not file.filename or not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF o Word (.docx)")

    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Categoría inválida. Debe ser una de: {', '.join(VALID_CATEGORIES)}",
        )

    file_path = settings.UPLOADS_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        doc_info = index_document(
            file_path=file_path,
            title=title,
            category=category,
            date=date or None,
        )
    except ValueError as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500, detail=f"Error al indexar documento: {str(e)}"
        )

    return DocumentUploadResponse(success=True, document=doc_info)


@router.get("")
def get_documents(category: str | None = Query(None, description="Filtrar por categoría")):
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Categoría inválida. Debe ser una de: {', '.join(VALID_CATEGORIES)}",
        )
    docs = list_documents(filter_category=category)
    for d in docs:
        d["downloadable"] = is_downloadable(d["id"], d.get("file_name", ""))
    return docs


@router.get("/{doc_id}/download")
def download_document(doc_id: str):
    """Descarga el archivo original de una ley de la bibliografía (solo las
    que tienen original disponible; ver app/core/originals.py)."""
    meta = next((m for m in get_metadata() if m.get("id") == doc_id), None)
    if not meta:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    path = find_original(doc_id, meta.get("file_name", ""))
    if path is None:
        raise HTTPException(status_code=404, detail="Este documento no está disponible para descarga.")
    filename = safe_download_name(meta.get("title", ""), path.stem) + path.suffix.lower()
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=filename)


@router.post("/{doc_id}/original", dependencies=[Depends(require_admin)])
async def attach_original(doc_id: str, file: UploadFile = File(...)):
    """Adjunta el PDF original a un documento ya indexado (por ejemplo uno
    que se indexó desde una transcripción de texto) para que se pueda
    descargar tal cual."""
    if not any(m.get("id") == doc_id for m in get_metadata()):
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El original debe ser un PDF")
    content = await file.read()
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido")
    save_original(doc_id, content)
    return {"success": True, "doc_id": doc_id, "bytes": len(content)}


@router.delete("/{doc_id}", dependencies=[Depends(require_admin)])
def remove_document(doc_id: str):
    try:
        delete_document(doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "detail": f"Documento '{doc_id}' eliminado"}


@router.post("/search")
def search_documents(
    query: str = Form(...),
    top_k: int = Form(5),
    filter_category: str | None = Form(None),
):
    if filter_category and filter_category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Categoría inválida. Debe ser una de: {', '.join(VALID_CATEGORIES)}",
        )
    results = search_legal_context(
        query=query, top_k=top_k, filter_category=filter_category
    )
    return {"query": query, "results": results, "count": len(results)}
