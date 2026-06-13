import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.database import (
    get_embedding_model,
    get_faiss_index,
    get_metadata,
    save_faiss_index,
)


def load_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def chunk_text(
    text: str, chunk_size: int = 1000, overlap: int = 200
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]


def index_document(
    file_path: Path,
    title: str,
    category: str,
    date: str | None = None,
) -> dict:
    text = load_pdf_text(file_path)
    if not text.strip():
        raise ValueError(f"El PDF '{file_path.name}' no contiene texto extraíble")

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError(f"No se pudieron generar fragmentos desde '{file_path.name}'")

    model = get_embedding_model()
    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    doc_id = str(uuid.uuid4())
    indexed_at = datetime.now(timezone.utc).isoformat()
    index = get_faiss_index(dimension=embeddings.shape[1])
    metadata = get_metadata()

    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        metadata.append(
            {
                "id": doc_id,
                "chunk_index": i,
                "title": title,
                "category": category,
                "date": date or "",
                "text": chunk,
                "indexed_at": indexed_at,
                "file_name": file_path.name,
            }
        )

    index.add(np.array(embeddings, dtype=np.float32))
    save_faiss_index()

    return {
        "id": doc_id,
        "title": title,
        "category": category,
        "chunks": len(chunks),
        "indexed_at": indexed_at,
    }


def search_legal_context(
    query: str,
    top_k: int = 5,
    filter_category: str | None = None,
) -> list[dict]:
    model = get_embedding_model()
    query_embedding = model.encode(
        [query], convert_to_numpy=True, normalize_embeddings=True
    )

    index = get_faiss_index()
    metadata = get_metadata()

    if index.ntotal == 0:
        return []

    if filter_category:
        filtered_indices = [
            i for i, m in enumerate(metadata) if m.get("category") == filter_category
        ]
        if not filtered_indices:
            return []

        filtered_vectors = np.array(
            [
                index.reconstruct(i)
                for i in filtered_indices
            ],
            dtype=np.float32,
        )

        import faiss

        sub_index = faiss.IndexFlatIP(query_embedding.shape[1])
        sub_index.add(filtered_vectors)

        k = min(top_k, len(filtered_indices))
        scores, sub_positions = sub_index.search(query_embedding, k)

        results = []
        for score, sub_pos in zip(scores[0], sub_positions[0]):
            if sub_pos == -1:
                continue
            original_idx = filtered_indices[sub_pos]
            entry = metadata[original_idx].copy()
            entry["score"] = float(score)
            results.append(entry)
        return results

    k = min(top_k, index.ntotal)
    scores, positions = index.search(query_embedding, k)

    results = []
    for score, pos in zip(scores[0], positions[0]):
        if pos == -1:
            continue
        entry = metadata[pos].copy()
        entry["score"] = float(score)
        results.append(entry)
    return results


def list_documents(filter_category: str | None = None) -> list[dict]:
    metadata = get_metadata()
    docs: dict[str, dict] = {}

    for entry in metadata:
        if filter_category and entry.get("category") != filter_category:
            continue
        doc_id = entry.get("id")
        if doc_id not in docs:
            docs[doc_id] = {
                "id": doc_id,
                "title": entry.get("title", ""),
                "category": entry.get("category", ""),
                "chunks": 0,
                "indexed_at": entry.get("indexed_at", ""),
                "date": entry.get("date", ""),
                "file_name": entry.get("file_name", ""),
            }
        docs[doc_id]["chunks"] += 1

    return sorted(docs.values(), key=lambda d: d["indexed_at"], reverse=True)


def delete_document(doc_id: str) -> None:
    metadata = get_metadata()
    indices_to_remove = [i for i, m in enumerate(metadata) if m.get("id") == doc_id]

    if not indices_to_remove:
        raise ValueError(f"Documento '{doc_id}' no encontrado en el índice")

    index = get_faiss_index()
    all_vectors = np.array(
        [index.reconstruct(i) for i in range(index.ntotal)], dtype=np.float32
    )

    keep_mask = np.ones(index.ntotal, dtype=bool)
    keep_mask[indices_to_remove] = False
    remaining_vectors = all_vectors[keep_mask]

    import faiss

    dimension = remaining_vectors.shape[1] if remaining_vectors.size > 0 else 384
    new_index = faiss.IndexFlatIP(dimension)
    if remaining_vectors.size > 0:
        new_index.add(remaining_vectors)

    import app.database as db

    db._faiss_index = new_index

    remaining_metadata = [m for i, m in enumerate(metadata) if i not in indices_to_remove]
    metadata.clear()
    metadata.extend(remaining_metadata)

    save_faiss_index()
