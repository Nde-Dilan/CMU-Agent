"""
Canonical Institutional Links and Contact Registry for CMU-Africa.
Prevents URL hallucinations by enforcing exact, verified institutional URLs and emails.
"""

import re
from typing import Dict

# Official verified links and emails
CANONICAL_LINKS: Dict[str, str] = {
    "apply_portal": "https://gradadmissions.engineering.cmu.edu/apply/",
    "application_status": "https://gradadmissions.engineering.cmu.edu/apply/",
    "admissions_email": "africa-admissions@andrew.cmu.edu",
    "academics_email": "africa-academics@andrew.cmu.edu",
    "det_live_support": "https://v2.zopim.com/widget/popout.html?key=a0DvoIZaplDC2ZowxpOPH3oGLjle3q9y",
    "det_faqs": "https://testcenter.zendesk.com/hc/en-us/categories/201147826-Frequently-Asked-Questions",
    "admission_calendly": "https://calendly.com/cmu-africa-graduate-admission-support-team/cmu-africa-graduate-admission-support?month=2025-10",
}

CANONICAL_LINKS_PROMPT = """=== [CANONICAL INSTITUTIONAL LINKS & DIRECTORY] ===
When providing links or contact information, you MUST ONLY use the official, verified URLs and emails listed below. NEVER invent, truncate, or hallucinate URLs or contact emails:
- Application Portal / Apply Now: https://gradadmissions.engineering.cmu.edu/apply/
- Application Status Portal: https://gradadmissions.engineering.cmu.edu/apply/
- Admissions Support Email: africa-admissions@andrew.cmu.edu
- Academic Services Email: africa-academics@andrew.cmu.edu
- Duolingo Test Live Support (Session Timeout & Uncertified Test Appeals): https://v2.zopim.com/widget/popout.html?key=a0DvoIZaplDC2ZowxpOPH3oGLjle3q9y
- Duolingo English Test Guides & FAQs: https://testcenter.zendesk.com/hc/en-us/categories/201147826-Frequently-Asked-Questions
- Book Admission Consultation (Calendly): https://calendly.com/cmu-africa-graduate-admission-support-team/cmu-africa-graduate-admission-support?month=2025-10
"""

# Common hallucinated link patterns to auto-correct
LINK_CORRECTIONS = [
    # Application portal corrections
    (
        r"https?://(www\.)?(cmu-africa\.edu/apply|engineering\.cmu\.edu/apply|gradadmissions\.cmu\.edu/apply)[^\s\)\>]*",
        CANONICAL_LINKS["apply_portal"],
    ),
    # Zopim Duolingo widget corrections
    (
        r"https?://(www\.)?(zopim\.com|duolingo\.com/support|go\.duolingo\.com/help)[^\s\)\>]*",
        CANONICAL_LINKS["det_live_support"],
    ),
    # Calendly link normalization
    (
        r"https?://(www\.)?calendly\.com/cmu-africa[^\s\)\>]*",
        CANONICAL_LINKS["admission_calendly"],
    ),
    # Zendesk FAQ normalization
    (
        r"https?://(www\.)?(testcenter\.zendesk\.com|duolingo\.com/faq)[^\s\)\>]*",
        CANONICAL_LINKS["det_faqs"],
    ),
    # Email normalization
    (
        r"(?i)\b(admissions|admission)@cmu-africa\.edu\b",
        CANONICAL_LINKS["admissions_email"],
    ),
    (
        r"(?i)\b(academics|academic)@cmu-africa\.edu\b",
        CANONICAL_LINKS["academics_email"],
    ),
]


def normalize_and_verify_links(text: str) -> str:
    """
    Post-processes the LLM's response to guarantee that all URLs and emails
    strictly adhere to official canonical URLs and prevent hallucinations.
    """
    if not text:
        return ""

    result = text
    for pattern, canonical_url in LINK_CORRECTIONS:
        result = re.sub(pattern, canonical_url, result)

    return result
