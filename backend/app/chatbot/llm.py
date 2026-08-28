from ollama import chat
from app.config import settings

MODEL_NAME = settings.OLLAMA_MODEL_NAME


def generate(messages: list) -> str:
    """
    Send a conversation to the local LLM
    and return the assistant's reply.
    """

    response = chat(
        model=MODEL_NAME,
        messages=messages,
    )

    return response.message.content