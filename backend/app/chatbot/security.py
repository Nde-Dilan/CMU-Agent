import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Standard refusal messages
OUT_OF_SCOPE_REFUSAL = (
    "ℹ️ *CMU-Africa Student Support Assistant*\n\n"
    "I can only assist with questions directly related to **CMU-Africa academic policies, "
    "degree requirements, student services, and the official Graduate Student Handbook**.\n\n"
    "Please ask a question related to your studies or student life at CMU-Africa!"
)

INJECTION_REFUSAL = (
    "⚠️ *Security Notice*\n\n"
    "I am programmed exclusively as the CMU-Africa Student Support Assistant. "
    "I cannot modify system instructions, execute arbitrary commands, or simulate other personas.\n\n"
    "How can I assist you with CMU-Africa academic guidelines or campus resources?"
)

# Common Prompt Injection & Jailbreak Signatures
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts|rules)",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)",
    r"(?i)you\s+are\s+now\s+(a|an|in)?\s*(dan|jailbreak|developer\s+mode|unrestricted|god\s+mode)",
    r"(?i)(reveal|show|print|output|display|repeat)\s+(your\s+)?(system\s+prompt|initial\s+prompt|hidden\s+instructions|system\s+instructions)",
    r"(?i)what\s+are\s+your\s+(system\s+instructions|system\s+prompts|rules\s+above)",
    r"(?i)bypass\s+(all\s+)?(safety|security|content\s+filters)",
    r"(?i)roleplay\s+as\s+(an?\s+)?unfiltered",
    r"(?i)pretend\s+you\s+(are\s+not|have\s+no)\s+rules",
    r"(?i)<\s*/?\s*(system|untrusted_student_input|institutional_handbook_content)\s*>",
]

# Simple Out-of-Scope Heuristics (e.g. arithmetic, trivia, poems)
OUT_OF_SCOPE_PATTERNS = [
    r"^\s*(\d+\s*[\+\-\*\/\^%]\s*\d+(\s*[\+\-\*\/\^%]\s*\d+)*)\s*\??\s*$",  # pure arithmetic: 2+3, 10*5, etc.
    r"(?i)^\s*(what\s+is\s+)?\d+\s*[\+\-\*\/]\s*\d+\s*\??\s*$",              # "what is 2+3"
    r"(?i)^\s*(tell\s+me\s+a\s+joke|write\s+a\s+(poem|song|story|essay\s+about\s+(cats|dogs|love|space)))\s*$",
    r"(?i)^\s*(who\s+won\s+the\s+world\s+cup|recipe\s+for\s+.*|how\s+to\s+cook\s+.*)\s*$",
]


def sanitize_student_input(text: str, max_length: int = 1500) -> str:
    """
    Sanitize untrusted student input:
    - Trims excessive length to prevent buffer/token attacks
    - Replaces prompt-boundary XML tags to prevent delimiter escape
    """
    if not text:
        return ""

    sanitized = text.strip()[:max_length]

    # Neutralize any attempts to inject XML structure tags
    sanitized = re.sub(
        r"<\s*/?\s*(system|application_policy|institutional_handbook_content|untrusted_student_input|instruction)\s*>",
        "[tag_removed]",
        sanitized,
        flags=re.IGNORECASE,
    )

    return sanitized


def is_prompt_injection(text: str) -> bool:
    """
    Check if the student input contains known prompt injection or jailbreak patterns.
    """
    if not text:
        return False

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text):
            logger.warning("Prompt injection signature detected: '%s' matched pattern '%s'", text, pattern)
            return True

    return False


def is_trivial_out_of_scope(text: str) -> bool:
    """
    Check if the query matches simple off-topic patterns (e.g. pure math, random jokes).
    """
    if not text:
        return False

    clean = text.strip()
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, clean):
            logger.info("Out-of-scope query pattern detected: '%s'", clean)
            return True

    return False
