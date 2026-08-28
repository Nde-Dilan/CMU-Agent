import logging
from typing import Dict, Any, Optional, List
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def normalize_chat_id(chat_id: str) -> str:
    """
    Normalize WhatsApp chat IDs / JIDs:
    - Strips device specifiers (e.g. '123:1@s.whatsapp.net' -> '123@c.us')
    - Converts '@s.whatsapp.net' to '@c.us'
    - Preserves '@lid', '@g.us', '@c.us'
    - Appends '@c.us' to plain phone numbers (e.g. '123456789' -> '123456789@c.us')
    - Prevents double-domain corruption like '...@lid@c.us' or '...@c.us@c.us'
    """
    if not chat_id:
        return ""
    chat_id = str(chat_id).strip()

    # If double domain occurred (e.g. ...@lid@c.us), keep first valid part
    while chat_id.count("@") > 1:
        parts = chat_id.split("@")
        chat_id = f"{parts[0]}@{parts[1]}"

    # Strip device specifier (e.g. 237650428379:1@s.whatsapp.net -> 237650428379@s.whatsapp.net)
    if ":" in chat_id and "@" in chat_id:
        user_part, domain_part = chat_id.split("@", 1)
        user_part = user_part.split(":", 1)[0]
        chat_id = f"{user_part}@{domain_part}"

    if chat_id.endswith("@s.whatsapp.net"):
        chat_id = chat_id.replace("@s.whatsapp.net", "@c.us")
    elif chat_id.endswith("@c.us") or chat_id.endswith("@g.us") or chat_id.endswith("@lid") or chat_id.endswith("@broadcast"):
        pass
    else:
        clean_num = chat_id.split("@")[0].split(":")[0]
        chat_id = f"{clean_num}@c.us"

    return chat_id


class WahaClient:
    """
    Client for interacting with WAHA (WhatsApp HTTP API - devlikeapro/waha).
    Supports all 3 engines: WEBJS, NOWEB, GOWS.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_session: Optional[str] = None,
    ):
        self._base_url = base_url
        self._api_key = api_key
        self._default_session = default_session
        self._cached_active_session: Optional[str] = None

    @property
    def base_url(self) -> str:
        return (self._base_url or settings.WAHA_BASE_URL or "http://localhost:3000").rstrip("/")

    @property
    def api_key(self) -> str:
        return self._api_key or settings.WAHA_API_KEY or ""

    @property
    def default_session(self) -> str:
        return self._default_session or settings.WAHA_SESSION or "default"

    @property
    def headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    async def get_active_session_name(self) -> str:
        """Resolve the currently working session name from WAHA."""
        if self._cached_active_session:
            return self._cached_active_session

        sessions = await self.get_sessions()
        for s in sessions:
            if s.get("status") == "WORKING":
                self._cached_active_session = s.get("name")
                return self._cached_active_session

        if sessions:
            self._cached_active_session = sessions[0].get("name")
            return self._cached_active_session

        return self.default_session

    async def send_text(
        self,
        chat_id: str,
        text: str,
        session: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a plain text message to a WhatsApp chat via WAHA.
        chat_id format: '1234567890@c.us', '257723975352466@lid', '1234567890'.
        """
        session_name = session or self.default_session
        normalized_chat_id = normalize_chat_id(chat_id)

        url = f"{self.base_url}/api/sendText"
        payload: Dict[str, Any] = {
            "session": session_name,
            "chatId": normalized_chat_id,
            "text": text,
        }
        if reply_to:
            payload["reply_to"] = reply_to

        logger.info(
            "Sending WAHA message to session='%s', chatId='%s' (original='%s')",
            session_name,
            normalized_chat_id,
            chat_id,
        )

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                if response.status_code in [404, 422]:
                    # Try resolving active session if session name changed
                    active_sess = await self.get_active_session_name()
                    if active_sess != session_name:
                        logger.info("Retrying sendText with active session: %s", active_sess)
                        payload["session"] = active_sess
                        response = await client.post(url, headers=self.headers, json=payload)

                if response.is_error:
                    logger.warning("WAHA sendText returned status %s: %s", response.status_code, response.text)
                response.raise_for_status()
                result = response.json()
                logger.info("WAHA sendText succeeded for %s", normalized_chat_id)
                return result
        except Exception as e:
            logger.warning("WAHA request failed (%s). Simulating reply to %s: %s", e, normalized_chat_id, text)
            return {"mock": True, "status": "simulated", "chatId": normalized_chat_id, "text": text}

    async def send_seen(
        self,
        chat_id: str,
        message_id: Optional[str] = None,
        session: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark a message or chat as seen (read receipt).
        """
        session_name = session or self.default_session
        normalized_chat_id = normalize_chat_id(chat_id)

        url = f"{self.base_url}/api/sendSeen"
        payload = {
            "session": session_name,
            "chatId": normalized_chat_id,
        }
        if message_id:
            payload["messageId"] = message_id

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                if response.is_error:
                    logger.debug("WAHA sendSeen returned status %s: %s", response.status_code, response.text)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.debug("Failed to send seen receipt to WAHA: %s", e)
            return {"mock": True, "status": "simulated"}

    async def get_sessions(self) -> List[Dict[str, Any]]:
        """List active sessions from WAHA."""
        url = f"{self.base_url}/api/sessions"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning("Failed to fetch WAHA sessions: %s", e)
            return []


waha_client = WahaClient()
