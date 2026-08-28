import logging
from typing import Optional, Any
from pywa import WhatsApp
from app.config import settings

logger = logging.getLogger(__name__)


def create_whatsapp_client(server: Optional[Any] = None) -> WhatsApp:
    """
    Factory to create and configure the PyWa WhatsApp Cloud API client.
    Attaches to the provided FastAPI server instance for automatic webhook handling.
    """
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID or "1234567890"
    token = settings.WHATSAPP_TOKEN or "mock_token"
    verify_token = settings.WHATSAPP_VERIFY_TOKEN or "cmu_agent_verify_token"

    validate_updates = bool(settings.WHATSAPP_APP_SECRET)

    wa = WhatsApp(
        phone_id=phone_id,
        token=token,
        server=server,
        verify_token=verify_token,
        webhook_endpoint="/webhook",
        validate_updates=validate_updates,
        app_id=settings.WHATSAPP_APP_ID or None,
        app_secret=settings.WHATSAPP_APP_SECRET or None,
    )
    return wa
