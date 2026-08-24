from ollama import chat

MODEL_NAME = "qwen3:8b"


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