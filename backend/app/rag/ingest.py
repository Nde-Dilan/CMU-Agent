import logging
import os
import sys
from pathlib import Path
from typing import Optional
from app.config import settings
from app.rag.document_loader import document_loader
from app.rag.vectorstore import vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag.ingest")


def resolve_source_path(custom_path: Optional[str] = None) -> str:
    """Resolve documents directory or fallback PDF path."""
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # 1. Check configured DOCUMENTS_DIR
    if os.path.exists(settings.DOCUMENTS_DIR):
        return settings.DOCUMENTS_DIR

    # 2. Check root 'documents' folder
    root_docs = Path(__file__).resolve().parent.parent.parent.parent / "documents"
    if root_docs.exists():
        return str(root_docs)

    # 3. Check single handbook path
    if os.path.exists(settings.HANDBOOK_PDF_PATH):
        return settings.HANDBOOK_PDF_PATH

    alt_pdf = Path(__file__).resolve().parent.parent.parent.parent / "CMU-Africa Graduate Handbook AY 25-26(final).pdf"
    if alt_pdf.exists():
        return str(alt_pdf)

    raise FileNotFoundError(f"No documents found at: {settings.DOCUMENTS_DIR} or {settings.HANDBOOK_PDF_PATH}")


def run_ingestion(source_path: Optional[str] = None, force_reindex: bool = False) -> int:
    """
    Ingest all CMU-Africa PDF documents into ChromaDB.
    Supports directories of PDFs as well as individual PDF files.
    """
    target_path = resolve_source_path(source_path)
    logger.info("Starting ingestion from source: %s", target_path)

    # Check if already indexed and not force reindex
    current_count = vector_store.count()
    if current_count > 0 and not force_reindex:
        logger.info(
            "Vector database already contains %d chunks in collection '%s'. "
            "Pass --force to re-process all documents.",
            current_count,
            settings.CHROMA_COLLECTION_NAME,
        )
        return current_count

    # Load chunks based on directory or single file
    if os.path.isdir(target_path):
        chunks = document_loader.load_directory(target_path)
    else:
        chunks = document_loader.load_pdf(target_path)

    if not chunks:
        logger.warning("No text chunks could be extracted from: %s", target_path)
        return 0

    logger.info("Extracted %d total chunks. Indexing into ChromaDB...", len(chunks))
    added = vector_store.add_chunks(chunks)
    logger.info(
        "Ingestion complete! Total documents in vector store collection '%s': %d",
        settings.CHROMA_COLLECTION_NAME,
        vector_store.count(),
    )
    return added


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    path_arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    try:
        run_ingestion(source_path=path_arg, force_reindex=force)
    except Exception as e:
        logger.error("Ingestion failed: %s", e, exc_info=True)
        sys.exit(1)
