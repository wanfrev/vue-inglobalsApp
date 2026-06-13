import shutil
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.config import settings
from app.core.rag import (
    delete_document,
    index_document,
    list_documents,
    search_legal_context,
)
from app.models.schemas import DocumentUploadResponse

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

VALID_CATEGORIES = {"venezolana", "internacional", "sostenibilidad"}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: Literal["venezolana", "internacional", "sostenibilidad"] = Form(...),
    date: str = Form(""),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

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
    return list_documents(filter_category=category)


@router.delete("/{doc_id}")
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
