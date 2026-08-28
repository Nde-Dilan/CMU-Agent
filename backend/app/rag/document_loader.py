import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    if not text:
        return ""
    # Replace multiple newlines or tabs with spaces/single newlines
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_page_link_annotations(page) -> List[str]:
    """
    Extract embedded hyperlinks/URIs from PDF page annotations (/Annots).
    This ensures embedded URLs behind clickable text are captured for RAG.
    """
    links: List[str] = []
    if "/Annots" not in page:
        return links

    try:
        annots = page.get("/Annots")
        if not annots:
            return links

        for annot in annots:
            try:
                obj = annot.get_object() if hasattr(annot, "get_object") else annot
                if isinstance(obj, dict) and "/A" in obj:
                    action = obj["/A"]
                    if hasattr(action, "get_object"):
                        action = action.get_object()
                    if isinstance(action, dict) and "/URI" in action:
                        uri = str(action["/URI"]).strip()
                        if uri and uri.startswith("http") and uri not in links:
                            links.append(uri)
            except Exception as e:
                logger.debug("Failed parsing annotation object: %s", e)
    except Exception as e:
        logger.debug("Failed reading page annotations: %s", e)

    return links


def chunk_text(
    text: str,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> List[str]:
    """
    Split text into chunks with sliding overlap, respecting paragraph/sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # If not at the end of the text, try to find a natural break point (paragraph or sentence)
        if end < text_len:
            # Look for double newline (paragraph break)
            last_break = text.rfind("\n\n", start, end)
            if last_break != -1 and last_break > start + (chunk_size // 2):
                end = last_break + 2
            else:
                # Look for sentence break (period, exclamation, question mark + space)
                last_period = max(
                    text.rfind(". ", start, end),
                    text.rfind(".\n", start, end),
                    text.rfind("? ", start, end),
                    text.rfind("! ", start, end),
                )
                if last_period != -1 and last_period > start + (chunk_size // 2):
                    end = last_period + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        start = max(end - chunk_overlap, start + 1)

    return chunks


def get_clean_source_title(file_name: str) -> str:
    """Derive a user-friendly source name from a PDF filename."""
    stem = Path(file_name).stem
    # Remove leading dates like 2026_08_26_
    stem = re.sub(r"^\d{4}[_\-]\d{2}[_\-]\d{2}[_\-]?", "", stem)
    # Common replacements
    name_map = {
        "CMU-Africa Graduate Handbook AY 25-26(final)": "CMU-Africa Graduate Handbook (AY 25-26)",
        "CMU-Africa WhatsApp Snippets": "CMU-Africa WhatsApp Snippets",
        "Duolingo English Test - FAQs": "Duolingo English Test FAQs",
        "DET Guide EN": "Duolingo English Test Guide",
        "GPN Test Rules 20260225": "GPN Test Rules",
    }
    return name_map.get(stem, stem.replace("_", " ").replace("-", " ").title())


def slugify_filename(file_name: str) -> str:
    """Create a short, safe slug for unique chunk IDs."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", Path(file_name).stem).strip("_").lower()
    return clean[:20]


class DocumentLoader:
    """
    Loads and processes PDF documents into structured chunks for RAG.
    Extracts visible text and underlying hyperlink annotations.
    """

    def __init__(
        self,
        chunk_size: int = 700,
        chunk_overlap: int = 120,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load a single PDF document, extract text and embedded links page by page, and split into chunks.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        file_name = os.path.basename(file_path)
        source_title = get_clean_source_title(file_name)
        file_slug = slugify_filename(file_name)
        logger.info("Loading PDF document from: %s (%s)", file_path, source_title)

        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        logger.info("PDF '%s' has %d pages", file_name, total_pages)

        all_chunks: List[Dict[str, Any]] = []

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            cleaned = clean_text(raw_text)

            # Extract embedded links from annotations
            embedded_links = extract_page_link_annotations(page)
            if embedded_links:
                links_text = "\n[Official Links on this page]:\n" + "\n".join(f"- {l}" for l in embedded_links)
                cleaned += links_text

            if not cleaned or len(cleaned) < 15:
                continue

            page_chunks = chunk_text(
                cleaned,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )

            for chunk_idx, chunk_text_content in enumerate(page_chunks):
                chunk_id = f"{file_slug}_p{page_num}_c{chunk_idx}"
                all_chunks.append(
                    {
                        "id": chunk_id,
                        "text": chunk_text_content,
                        "metadata": {
                            "source": source_title,
                            "file_name": file_name,
                            "page": page_num,
                            "chunk_index": chunk_idx,
                            "total_pages": total_pages,
                        },
                    }
                )

        logger.info(
            "Extracted %d chunks across %d pages from '%s'",
            len(all_chunks),
            total_pages,
            file_name,
        )
        return all_chunks

    def load_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """
        Load all PDF files in a directory and return aggregated chunks.
        """
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Documents directory not found at: {dir_path}")

        pdf_files = [
            os.path.join(dir_path, f)
            for f in os.listdir(dir_path)
            if f.lower().endswith(".pdf")
        ]

        if not pdf_files:
            logger.warning("No PDF files found in directory: %s", dir_path)
            return []

        logger.info("Found %d PDF document(s) in %s", len(pdf_files), dir_path)
        combined_chunks: List[Dict[str, Any]] = []

        for pdf_path in sorted(pdf_files):
            try:
                chunks = self.load_pdf(pdf_path)
                combined_chunks.extend(chunks)
            except Exception as e:
                logger.error("Error loading PDF '%s': %s", pdf_path, e, exc_info=True)

        logger.info(
            "Total chunks extracted from %d documents: %d chunks",
            len(pdf_files),
            len(combined_chunks),
        )
        return combined_chunks


document_loader = DocumentLoader()
