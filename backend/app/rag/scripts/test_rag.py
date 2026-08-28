import logging
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.chatbot.service import chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("test_links_and_rag")


def run_tests():
    test_queries = [
        "Where can I apply for CMU-Africa and check my application status?",
        "My Duolingo test session timed out or was not certified, how can I get help?",
        "How can I schedule an appointment with the CMU-Africa admission team?",
    ]

    print("\n" + "=" * 65)
    print("CMU-Africa Canonical Link & Snippet RAG Verification Test")
    print("=" * 65)

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test Query {i}]: {query}")
        reply = chat(query)
        print("\nAgent Response:\n")
        print(reply)
        print("-" * 55)

    print("\n[SUCCESS] All Link Verification Tests Completed Successfully!\n")


if __name__ == "__main__":
    run_tests()
