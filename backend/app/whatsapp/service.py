import logging
from typing import Dict, List, Optional
from pywa import WhatsApp
from pywa.types import Message
from app.chatbot.service import chat as agent_chat
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the CMU Student Support Assistant on WhatsApp. "
    "Your goal is to help Carnegie Mellon University (CMU) students with academic, "
    "administrative, and campus life questions. "
    "Keep your answers helpful, concise, well-structured, and clear. "
    "Use WhatsApp formatting where appropriate (*bold*, _italic_, bullet points). "
    "If you do not know the answer, politely advise contacting CMU Student Affairs or the relevant department."
)


class WhatsAppService:
    """
    Service handling WhatsApp bot business logic, conversation state,
    and dispatching to the CMU Agent LLM/RAG pipeline using PyWa.
    """

    def __init__(self, max_history_turns: int = 6):
        self.max_history_turns = max_history_turns
        # In-memory history cache: {phone_number: [ {"role": "...", "content": "..."} ]}
        self.conversation_sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_session_history(self, sender_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history for a given phone number, initializing with system prompt if new."""
        if sender_id not in self.conversation_sessions:
            self.conversation_sessions[sender_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self.conversation_sessions[sender_id]

    def add_to_session(self, sender_id: str, role: str, content: str) -> None:
        """Append message to session history and trim if it exceeds history window."""
        history = self.get_session_history(sender_id)
        history.append({"role": role, "content": content})

        # Keep system prompt + last N messages
        if len(history) > (self.max_history_turns * 2 + 1):
            system_msg = history[0]
            recent_msgs = history[-(self.max_history_turns * 2):]
            self.conversation_sessions[sender_id] = [system_msg] + recent_msgs

    def clear_session(self, sender_id: str) -> None:
        """Reset conversation session for a sender."""
        self.conversation_sessions.pop(sender_id, None)

    def process_message_text(self, sender_id: str, message_text: str) -> str:
        """
        Process user text input with the chatbot service and update session state.
        """
        # Check for reset/restart command
        if message_text.strip().lower() in ["/reset", "/clear", "reset", "start"]:
            self.clear_session(sender_id)
            return (
                "👋 *Hello! Welcome to the CMU Student Support Assistant.* \n\n"
                "I am here to assist you with questions regarding courses, campus services, "
                "policies, and student life at CMU. How can I help you today?"
            )

        # Get conversation history
        history = self.get_session_history(sender_id)

        try:
            # Generate response from chatbot service
            response_text = agent_chat(user_message=message_text, history=history)
        except Exception as e:
            logger.error("Error generating chatbot response: %s", e, exc_info=True)
            response_text = (
                "⚠️ I'm sorry, I encountered an issue processing your request. "
                "Please make sure Ollama is running, or contact CMU Student Support."
            )

        # Update session memory
        self.add_to_session(sender_id, "user", message_text)
        self.add_to_session(sender_id, "assistant", response_text)

        return response_text

    def handle_pywa_message(self, wa: WhatsApp, msg: Message) -> None:
        """
        PyWa handler callback triggered when a WhatsApp message update arrives.
        """
        sender_id = msg.sender
        logger.info("Received WhatsApp message from %s (type: %s)", sender_id, msg.type)

        # Mark message as read
        try:
            msg.mark_as_read()
        except Exception as e:
            logger.debug("Failed to mark message as read: %s", e)

        if msg.text:
            reply_text = self.process_message_text(sender_id=sender_id, message_text=msg.text)
        else:
            reply_text = (
                "ℹ️ Thanks for reaching out! Currently, I can only process text messages. "
                "Please send your question in text."
            )

        # Send response back to user
        try:
            if settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
                msg.reply_text(text=reply_text)
            else:
                logger.info("[MOCK MODE] Simulated reply to %s: %s", sender_id, reply_text)
        except Exception as e:
            logger.error("Failed to send WhatsApp message via PyWa: %s", e, exc_info=True)


whatsapp_service = WhatsAppService()
