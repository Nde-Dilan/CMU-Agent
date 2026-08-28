import logging
from typing import List
import httpx
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    ChromaDB compatible EmbeddingFunction that queries a local Ollama instance.
    Uses 'nomic-embed-text' or configured embedding model.
    """

    def __init__(
        self,
        model_name: Optional_str = None,
        base_url: Optional_str = None,
    ):
        self.model_name = model_name or settings.OLLAMA_EMBED_MODEL_NAME
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    def __call__(self, input: Documents) -> Embeddings:
        """Embed a list of text documents synchronously for ChromaDB."""
        if not input:
            return []

        embeddings: List[List[float]] = []
        with httpx.Client(timeout=60.0) as client:
            for text in input:
                try:
                    # Ollama /api/embeddings endpoint
                    response = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model_name, "prompt": text},
                    )
                    response.raise_for_status()
                    data = response.json()
                    embeddings.append(data["embedding"])
                except Exception as e:
                    logger.error("Error generating embedding for text snippet: %s", e)
                    # Fallback to Ollama /api/embed (newer endpoint in Ollama >= 0.1.30)
                    try:
                        res = client.post(
                            f"{self.base_url}/api/embed",
                            json={"model": self.model_name, "input": text},
                        )
                        res.raise_for_status()
                        emb = res.json().get("embeddings", [[]])[0]
                        embeddings.append(emb)
                    except Exception as fallback_err:
                        logger.error("Fallback embed endpoint also failed: %s", fallback_err)
                        raise e

        return embeddings

    async def aembed_query(self, query: str) -> List[float]:
        """Embed a single query string asynchronously."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model_name, "prompt": query},
                )
                response.raise_for_status()
                return response.json()["embedding"]
            except Exception:
                res = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model_name, "input": query},
                )
                res.raise_for_status()
                return res.json()["embeddings"][0]


# Type alias for Optional[str]
from typing import Optional as Optional_str

ollama_embedding_function = OllamaEmbeddingFunction()
