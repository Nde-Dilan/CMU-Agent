import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

class Settings:
    # LLM & Embedding Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL_NAME", "qwen3:8b")
    OLLAMA_EMBED_MODEL_NAME: str = os.getenv("OLLAMA_EMBED_MODEL_NAME", "nomic-embed-text")

    # RAG Settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "cmu_handbook")
    DOCUMENTS_DIR: str = os.getenv("DOCUMENTS_DIR", str(ROOT_DIR / "documents"))
    HANDBOOK_PDF_PATH: str = os.getenv(
        "HANDBOOK_PDF_PATH",
        str(ROOT_DIR / "documents" / "CMU-Africa Graduate Handbook AY 25-26(final).pdf"),
    )
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))

    # WhatsApp Filter Settings: Only reply to private 1-on-1 DMs by default
    ALLOW_GROUP_MESSAGES: bool = os.getenv("ALLOW_GROUP_MESSAGES", "false").lower() in ("true", "1", "yes")

    # Active Engine: 'waha' for open-source PoC, 'meta' for official Meta Cloud API
    WHATSAPP_ENGINE: str = os.getenv("WHATSAPP_ENGINE", "waha")

    # WAHA (WhatsApp HTTP API - devlikeapro/waha) Settings
    WAHA_BASE_URL: str = os.getenv("WAHA_BASE_URL", "http://localhost:3000")
    WAHA_API_KEY: str = os.getenv("WAHA_API_KEY", "")
    WAHA_SESSION: str = os.getenv("WAHA_SESSION", "default")

    # WhatsApp Cloud API Settings (Meta for Developers)
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "cmu_agent_verify_token")
    WHATSAPP_API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "21.0")
    WHATSAPP_BASE_URL: str = os.getenv("WHATSAPP_BASE_URL", "https://graph.facebook.com")
    WHATSAPP_APP_ID: str = os.getenv("WHATSAPP_APP_ID", "")
    WHATSAPP_APP_SECRET: str = os.getenv("WHATSAPP_APP_SECRET", "")

settings = Settings()
