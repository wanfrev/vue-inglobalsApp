"""Archivos originales de la bibliografía que el usuario puede DESCARGAR.

A pedido del cliente, quien consulta una ley de la bibliografía puede
descargarla (en PDF) — pero solo las leyes, no el resto del catálogo (manuales
y libros con derechos de autor). Un documento es descargable si:

1. se le adjuntó su archivo original (POST /documents/{id}/original), que se
   guarda en UPLOADS_DIR/originals/{id}.pdf; o
2. su archivo (el mismo `file_name` con el que se indexó) está en la carpeta de
   leyes del repo (settings.LAWS_DIR_NAME, "Biblioteca_Leyes_Vzla").
"""
import time
from pathlib import Path

from app.config import settings

_LAWS_TTL_SECONDS = 60
_laws_cache: dict = {"at": 0.0, "files": {}}

# La carpeta de leyes trae algún manual con derechos de autor (ej. el Código de
# Ética del IESBA/IFAC): no se ofrece para descargar, solo se usa para consultar.
_EXCLUDED_NAME_PARTS = ("iesba", "manual")

# Caracteres que no pueden ir en un nombre de archivo (Windows/Linux).
_FORBIDDEN_IN_FILENAMES = {chr(92), "/", ":", "*", "?", '"', "<", ">", "|", chr(10), chr(13)}


def originals_dir() -> Path:
    path = settings.UPLOADS_DIR / "originals"
    path.mkdir(parents=True, exist_ok=True)
    return path


def laws_dir() -> Path:
    return settings.BASE_DIR.parent / settings.LAWS_DIR_NAME


def _law_files() -> dict[str, Path]:
    now = time.monotonic()
    if now - _laws_cache["at"] > _LAWS_TTL_SECONDS:
        folder = laws_dir()
        files: dict[str, Path] = {}
        if folder.is_dir():
            for p in folder.rglob("*"):
                if p.is_file() and p.suffix.lower() in (".pdf", ".docx"):
                    if any(part in p.name.lower() for part in _EXCLUDED_NAME_PARTS):
                        continue
                    files[p.name.lower()] = p
        _laws_cache.update(at=now, files=files)
    return _laws_cache["files"]


def find_original(doc_id: str, file_name: str = "") -> Path | None:
    if doc_id:
        attached = originals_dir() / f"{doc_id}.pdf"
        if attached.is_file():
            return attached
    if file_name:
        return _law_files().get(file_name.lower())
    return None


def is_downloadable(doc_id: str, file_name: str = "") -> bool:
    return find_original(doc_id, file_name) is not None


def save_original(doc_id: str, content: bytes) -> Path:
    path = originals_dir() / f"{doc_id}.pdf"
    path.write_bytes(content)
    return path


def safe_download_name(title: str, fallback: str = "documento") -> str:
    cleaned = "".join(" " if c in _FORBIDDEN_IN_FILENAMES else c for c in (title or ""))
    name = " ".join(cleaned.split())[:120].strip(" .")
    return name or fallback
