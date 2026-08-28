import logging
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.rag.vectorstore import vector_store

logger = logging.getLogger(__name__)


def format_context_for_llm(matches: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """
    Format retrieved vector search matches into a structured context block with document and page citations.
    Returns: (formatted_context_str, list_of_citations)
    """
    if not matches:
        return "", []

    context_blocks: List[str] = []
    citations: List[str] = []

    for i, match in enumerate(matches, 1):
        meta = match.get("metadata", {})
        page = meta.get("page", "?")
        source = meta.get("source", "CMU-Africa Document")
        text = match.get("text", "").strip()

        citation = f"{source} (Page {page})"
        if citation not in citations:
            citations.append(citation)

        block = f"[Excerpt {i} | {citation}]\n{text}"
        context_blocks.append(block)

    formatted_context = "\n\n---\n\n".join(context_blocks)
    return formatted_context, citations


class Retriever:
    """
    Retrieves and formats relevant context from CMU-Africa institutional documents.
    """

    def __init__(self, top_k: int = 4):
        self.top_k = top_k

    def get_relevant_context(
        self,
        query: str,
        top_k: int = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant institutional document chunks and format for prompt augmentation.
        Returns:
        {
            "context": "...",
            "citations": ["CMU-Africa Graduate Handbook (AY 25-26) (Page 12)", ...],
            "matches": [...]
        }
        """
        k = top_k or self.top_k or settings.RAG_TOP_K
        matches = vector_store.query(query_text=query, top_k=k)

        if not matches:
            logger.info("No matching context found for query: '%s'", query)
            return {
                "context": "",
                "citations": [],
                "matches": [],
            }

        context_str, citations = format_context_for_llm(matches)
        logger.info(
            "Retrieved %d chunks (citations: %s) for query: '%s'",
            len(matches),
            citations,
            query,
        )

        return {
            "context": context_str,
            "citations": citations,
            "matches": matches,
        }


retriever = Retriever()
