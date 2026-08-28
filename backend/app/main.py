import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.whatsapp.router import router as whatsapp_router
from app.rag.vectorstore import vector_store
from app.rag.ingest import run_ingestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup & shutdown lifecycle handler.
    Checks if ChromaDB vector store is populated, auto-ingests handbook if empty.
    """
    try:
        count = vector_store.count()
        if count == 0:
            logger.info("ChromaDB vector store is empty. Triggering background ingestion...")
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, run_ingestion)
        else:
            logger.info("RAG Vector Store ready with %d indexed chunks.", count)
    except Exception as e:
        logger.warning("Could not verify RAG vector store on startup: %s", e)

    yield


# 1. Initialize FastAPI Application
app = FastAPI(
    title="CMU Student Support Agent API",
    description="Backend API and WhatsApp Bot Integration with RAG for CMU Student Support Agent",
    version="0.2.0",
    lifespan=lifespan,
)

# 2. Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register WhatsApp Webhook Router (WAHA & Meta)
app.include_router(whatsapp_router)


@app.get("/")
def root():
    return {
        "name": "CMU-Africa Student Support Agent",
        "status": "online",
        "rag_status": "ready" if vector_store.count() > 0 else "indexing",
        "indexed_chunks": vector_store.count(),
        "active_engine": settings.WHATSAPP_ENGINE,
        "waha_endpoint": "/webhook/waha",
        "llm_model": settings.OLLAMA_MODEL_NAME,
        "embed_model": settings.OLLAMA_EMBED_MODEL_NAME,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "engine": settings.WHATSAPP_ENGINE,
        "llm_model": settings.OLLAMA_MODEL_NAME,
        "embed_model": settings.OLLAMA_EMBED_MODEL_NAME,
        "indexed_chunks": vector_store.count(),
    }
