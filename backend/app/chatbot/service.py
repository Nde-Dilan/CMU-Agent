from app.chatbot.llm import generate


def chat(user_message: str) -> str:
    """
    Handle a user's message and return the model's response.
    """

    messages = [
        {
            "role": "user",
            "content": user_message,
        }
    ]

    return generate(messages)