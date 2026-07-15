"""
claim_extractor.py

Extracts the factual claim into:

Subject
Relation
Object
"""

import re

RELATION_PATTERNS = [
    " is the ",
    " is a ",
    " is an ",
    " was the ",
    " was a ",
    " was an ",
    " became ",
    " becomes ",
    " serves as ",
    " works as ",
    " owns ",
    " founded ",
    " created ",
    " invented ",
    " married ",
    " defeated ",
    " won ",
    " lost ",
]


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def extract_claim(text: str):
    """
    Returns:

    {
        "subject": "...",
        "relation": "...",
        "object": "...",
        "claim": "..."
    }
    """

    text = normalize_text(text)

    lower = text.lower()

    for relation in RELATION_PATTERNS:

        idx = lower.find(relation)

        if idx != -1:

            subject = text[:idx].strip()

            obj = text[idx + len(relation):].strip()

            return {
                "subject": subject,
                "relation": relation.strip(),
                "object": obj,
                "claim": text,
            }

    return {
        "subject": "",
        "relation": "",
        "object": "",
        "claim": text,
    }


def is_fact_claim(text: str):

    claim = extract_claim(text)

    return (
        len(claim["subject"]) > 0
        and len(claim["relation"]) > 0
        and len(claim["object"]) > 0
    )