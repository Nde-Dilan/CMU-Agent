import logging
from typing import Dict, List, Optional, Any, Set
from collections import deque
from app.config import settings
from app.chatbot.service import chat as agent_chat
from app.whatsapp.waha_client import waha_client, WahaClient

logger = logging.getLogger(__name__)

# System Prompt customized for CMU WhatsApp Assistant
SYSTEM_PROMPT = (
    "You are the CMU Student Support Assistant on WhatsApp. "
    "Your goal is to help Carnegie Mellon University (CMU) students with academic, "
    "administrative, and campus life questions. "
    "Keep your answers helpful, concise, well-structured, and clear. "
    "Use WhatsApp formatting where appropriate (*bold*, _italic_, bullet points). "
    "If you do not know the answer, politely advise contacting CMU Student Affairs or the relevant department."
)


class WahaService:
    """
    Business logic layer for processing WAHA (WhatsApp HTTP API) webhook events.
    Handles message deduplication, multi-turn history, group chat filtering, and Ollama agent routing.
    """

    def __init__(self, client: Optional[WahaClient] = None, max_history_turns: int = 6):
        self.client = client or waha_client
        self.max_history_turns = max_history_turns
        # In-memory history per chat: {chatId: [ {"role": "...", "content": "..."} ]}
        self.conversation_sessions: Dict[str, List[Dict[str, str]]] = {}
        # Message ID deduplication cache (stores last 500 processed message IDs)
        self.processed_message_ids: Set[str] = set()
        self.recent_ids_queue: deque = deque(maxlen=500)

    def get_session_history(self, chat_id: str) -> List[Dict[str, str]]:
        """Retrieve or initialize conversation history for a chat."""
        if chat_id not in self.conversation_sessions:
            self.conversation_sessions[chat_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self.conversation_sessions[chat_id]

    def add_to_session(self, chat_id: str, role: str, content: str) -> None:
        """Add a message turn to the session and trim to sliding window."""
        history = self.get_session_history(chat_id)
        history.append({"role": role, "content": content})

        # Keep system prompt + last N turns
        if len(history) > (self.max_history_turns * 2 + 1):
            system_msg = history[0]
            recent_msgs = history[-(self.max_history_turns * 2):]
            self.conversation_sessions[chat_id] = [system_msg] + recent_msgs

    def clear_session(self, chat_id: str) -> None:
        """Reset conversation context for a chat."""
        self.conversation_sessions.pop(chat_id, None)

    def is_duplicate(self, message_id: Optional[str]) -> bool:
        """Check and record message ID to prevent duplicate processing."""
        if not message_id:
            return False
        if message_id in self.processed_message_ids:
            return True

        self.processed_message_ids.add(message_id)
        if len(self.recent_ids_queue) == self.recent_ids_queue.maxlen:
            oldest = self.recent_ids_queue.popleft()
            self.processed_message_ids.discard(oldest)
        self.recent_ids_queue.append(message_id)
        return False

    def is_group_or_broadcast(self, payload: Dict[str, Any]) -> bool:
        """
        Determine if the incoming message is from a group chat, channel, or broadcast.
        """
        from_id = str(payload.get("from") or "").lower().strip()
        chat_id = str(payload.get("chatId") or "").lower().strip()
        to_id = str(payload.get("to") or "").lower().strip()
        participant = payload.get("participant") or payload.get("author")

        # 1. Direct group flag from WAHA
        if payload.get("isGroup") is True or payload.get("group") is True:
            return True

        # 2. Group JID pattern (@g.us)
        if from_id.endswith("@g.us") or chat_id.endswith("@g.us") or to_id.endswith("@g.us"):
            return True

        # 3. Broadcast, newsletter, or status updates
        if (
            from_id.endswith("@broadcast")
            or chat_id.endswith("@broadcast")
            or from_id.endswith("@newsletter")
            or chat_id.endswith("@newsletter")
            or "status@broadcast" in from_id
            or "status@broadcast" in chat_id
        ):
            return True

        # 4. Multi-participant group context
        if participant and (from_id.endswith("@g.us") or chat_id.endswith("@g.us")):
            return True

        return False

    def extract_sender_chat_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract the best target chat ID from WAHA message payload."""
        from_id = payload.get("from")
        chat_id = payload.get("chatId")
        author_id = payload.get("author") or payload.get("participant")

        # Check nested _data.key if present
        key_data = payload.get("_data", {}).get("key", {}) if isinstance(payload.get("_data"), dict) else {}
        remote_jid = key_data.get("remoteJid")

        # Check message ID format (e.g. false_237650428379@c.us_3EB0...)
        id_remote_jid = None
        msg_id = payload.get("id")
        if msg_id and isinstance(msg_id, str) and "_" in msg_id:
            parts = msg_id.split("_")
            if len(parts) >= 3 and "@" in parts[1]:
                id_remote_jid = parts[1]

        candidates = [from_id, chat_id, remote_jid, id_remote_jid, author_id]

        # If groups are disabled, exclude @g.us / broadcast candidates
        if not getattr(settings, "ALLOW_GROUP_MESSAGES", False):
            candidates = [
                c for c in candidates
                if c and not str(c).strip().endswith(("@g.us", "@broadcast", "@newsletter"))
            ]

        # Prioritize phone number JIDs (@c.us or @s.whatsapp.net) first
        for candidate in candidates:
            if candidate and isinstance(candidate, str):
                c_clean = candidate.strip()
                if c_clean.endswith("@c.us") or c_clean.endswith("@s.whatsapp.net"):
                    return c_clean

        # If no @c.us found, use first valid candidate with domain (@lid, etc.)
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and "@" in candidate:
                return candidate.strip()

        return from_id or chat_id or remote_jid

    async def process_user_query(self, chat_id: str, text: str) -> str:
        """
        Run user query through chatbot service with conversation history.
        """
        if text.strip().lower() in ["/reset", "/clear", "reset", "start"]:
            self.clear_session(chat_id)
            return (
                "👋 *Hello! Welcome to the CMU Student Support Assistant.* \n\n"
                "I am here to assist you with questions regarding courses, campus services, "
                "policies, and student life at CMU. How can I help you today?"
            )

        history = self.get_session_history(chat_id)

        try:
            reply = agent_chat(user_message=text, history=history)
        except Exception as e:
            logger.error("Chatbot processing error: %s", e, exc_info=True)
            reply = (
                "⚠️ I'm sorry, I encountered an issue processing your request. "
                "Please check that Ollama is running, or contact CMU Student Support."
            )

        self.add_to_session(chat_id, "user", text)
        self.add_to_session(chat_id, "assistant", reply)
        return reply

    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Parse and process an incoming event from WAHA.
        Filters out bot self-messages, group chats, status updates, and duplicate messages.
        """
        event_name = str(event_data.get("event", ""))
        # Only process message events, ignore status updates (e.g. message.ack)
        if not (event_name == "message" or event_name == "message.any" or event_name == "message.upsert"):
            logger.debug("Ignoring non-message WAHA event: %s", event_name)
            return None

        payload = event_data.get("payload", {})
        session_name = event_data.get("session", "default")

        # 1. Ignore messages sent by the bot itself to prevent infinite feedback loops
        if payload.get("fromMe", False):
            logger.debug("Ignoring message sent by bot (fromMe=True)")
            return None

        # 2. Ignore group chats, channels, and broadcasts (Private DMs only)
        if not getattr(settings, "ALLOW_GROUP_MESSAGES", False) and self.is_group_or_broadcast(payload):
            logger.info(
                "Silently ignoring group/broadcast message from '%s' (Bot is configured for private DMs only)",
                payload.get("from") or payload.get("chatId"),
            )
            return None

        # 3. Deduplicate message ID
        msg_id = payload.get("id")
        if self.is_duplicate(msg_id):
            logger.debug("Ignoring duplicate message ID: %s", msg_id)
            return None

        # 4. Extract sender chat ID
        chat_id = self.extract_sender_chat_id(payload)
        if not chat_id:
            logger.warning("WAHA message received without sender chat_id: %s", payload)
            return None

        # Acknowledge read receipt
        if msg_id:
            await self.client.send_seen(chat_id=chat_id, message_id=msg_id, session=session_name)

        # 5. Extract message body
        body = payload.get("body") or payload.get("text")
        if not body:
            fallback = (
                "ℹ️ Thanks for reaching out! Currently, I can only process text messages. "
                "Please type your question."
            )
            await self.client.send_text(chat_id=chat_id, text=fallback, session=session_name, reply_to=msg_id)
            return fallback

        logger.info("Processing private WAHA message from %s: %s", chat_id, body)
        reply_text = await self.process_user_query(chat_id=chat_id, text=body)

        # 6. Send response via WAHA
        await self.client.send_text(
            chat_id=chat_id,
            text=reply_text,
            session=session_name,
            reply_to=msg_id,
        )
        return reply_text


waha_service = WahaService()
