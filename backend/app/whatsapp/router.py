import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from app.config import settings
from app.whatsapp.waha_service import waha_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhooks"])


# ==========================================
# WAHA (devlikeapro/waha) Webhook Endpoints
# ==========================================

@router.get("/waha")
async def waha_health():
    """Healthcheck endpoint for WAHA webhook setup."""
    return {
        "status": "active",
        "engine": "WAHA (devlikeapro/waha)",
        "waha_base_url": settings.WAHA_BASE_URL,
        "session": settings.WAHA_SESSION,
    }


@router.post("/waha")
async def receive_waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Inbound webhook endpoint called by WAHA when events occur (e.g. message received).
    Dispatches to WahaService asynchronously in background tasks.
    """
    try:
        event_data: Dict[str, Any] = await request.json()
    except Exception as e:
        logger.error("Failed to parse WAHA JSON body: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.debug("Received WAHA event: %s", event_data.get("event"))

    # Process in background to return 200 OK immediately
    background_tasks.add_task(waha_service.handle_webhook_event, event_data)

    return {"status": "ok"}


# ==========================================
# Developer Simulator & Meta Fallback
# ==========================================

@router.post("/test-message")
async def simulate_incoming_message(sender: str = "237690000000", text: str = "Hello CMU Agent"):
    """
    Developer testing endpoint to simulate an incoming message
    and immediately return the assistant's reply.
    """
    chat_id = f"{sender}@c.us" if not sender.endswith("@c.us") else sender
    reply = await waha_service.process_user_query(chat_id=chat_id, text=text)
    return {
        "chat_id": chat_id,
        "query": text,
        "reply": reply,
    }


@router.get("")
async def meta_webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Meta Graph API Webhook Verification handshake (kept ready for when CMU activates Meta).
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge or "", status_code=200)
    raise HTTPException(status_code=403, detail="Verification token mismatch")
