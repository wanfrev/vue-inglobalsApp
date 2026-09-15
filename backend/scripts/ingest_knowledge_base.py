"""Indexa de una vez toda la base de conocimiento del Simulador DAD en el
índice FAISS local (RAG). Se corre una sola vez (o cada vez que se agreguen
documentos nuevos) desde la carpeta `backend`:

    python scripts/ingest_knowledge_base.py

Carpetas de origen (relativas a la raíz del repo, un nivel arriba de
`backend/`) y la categoría con la que se indexa cada una:

- Bibliografia/                                          -> metodologica
- Bibliografia_pocesos_contables_sector_publico_vzla/    -> venezolana
- Biblioteca_Leyes_Vzla/                                 -> venezolana
- Biblioteca_colegio_contadores_publicos/                -> internacional
- bibliografa_diplomado/                                 -> internacional

"metodologica" alimenta el Prompt 1 (organizador): son los 3 anexos
epistemológicos (Chalmers, Bunge, Searle) que le dan al modelo la lógica y el
orden para estructurar cualquier consulta, no contenido legal. El resto
alimenta el Prompt 2 (validador), que sí necesita el contexto legal/normativo
real para el veredicto DAD.

Se admiten archivos .pdf y .docx. Se ignoran silenciosamente: archivos de
bloqueo de Word (`~$...`), `desktop.ini`, y formatos sin soporte de
extracción de texto (ej. .rar) — estos últimos se reportan al final para que
se extraigan manualmente si se quieren incluir.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.rag import index_document  # noqa: E402
from app.database import get_metadata, init_sqlite  # noqa: E402

FOLDER_CATEGORY_MAP = {
    "Bibliografia": "metodologica",
    "Bibliografia_pocesos_contables_sector_publico_vzla": "venezolana",
    "Biblioteca_Leyes_Vzla": "venezolana",
    "Biblioteca_colegio_contadores_publicos": "internacional",
    "bibliografa_diplomado": "internacional",
}

SUPPORTED_SUFFIXES = {".pdf", ".docx"}


def _is_indexable(file_path: Path) -> bool:
    if file_path.name.startswith("~$"):
        return False
    if file_path.name.lower() == "desktop.ini":
        return False
    return file_path.suffix.lower() in SUPPORTED_SUFFIXES


def main() -> None:
    init_sqlite()
    already_indexed = {m.get("file_name") for m in get_metadata()}

    indexed, skipped_existing, unsupported, failed = [], [], [], []

    for folder_name, category in FOLDER_CATEGORY_MAP.items():
        folder = REPO_ROOT / folder_name
        if not folder.is_dir():
            print(f"[AVISO] Carpeta no encontrada, se omite: {folder}")
            continue

        for file_path in sorted(folder.rglob("*")):
            if not file_path.is_file():
                continue

            if not _is_indexable(file_path):
                if file_path.suffix.lower() not in (".ini",) and not file_path.name.startswith("~$"):
                    unsupported.append(file_path)
                continue

            if file_path.name in already_indexed:
                skipped_existing.append(file_path)
                continue

            print(f"Indexando [{category}] {file_path.relative_to(REPO_ROOT)} ...")
            try:
                info = index_document(
                    file_path=file_path,
                    title=file_path.stem,
                    category=category,
                )
                indexed.append((file_path, info["chunks"]))
                already_indexed.add(file_path.name)
            except Exception as e:
                print(f"  [ERROR] {e}")
                failed.append((file_path, str(e)))

    print("\n--- Resumen ---")
    print(f"Indexados ahora: {len(indexed)}")
    for f, chunks in indexed:
        print(f"  + {f.relative_to(REPO_ROOT)} ({chunks} fragmentos)")
    print(f"Ya estaban indexados (se omiten): {len(skipped_existing)}")
    if failed:
        print(f"Fallaron: {len(failed)}")
        for f, err in failed:
            print(f"  - {f.relative_to(REPO_ROOT)}: {err}")
    if unsupported:
        print(f"Formato no soportado, requieren extracción manual ({len(unsupported)}):")
        for f in unsupported:
            print(f"  ~ {f.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
