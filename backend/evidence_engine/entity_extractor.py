import re
from typing import Dict


RELATIONS = [
    "is",
    "was",
    "are",
    "were",
    "won",
    "beat",
    "bombed",
    "attacked",
    "appointed",
    "elected",
    "resigned",
    "became",
    "launched",
    "announced",
    "introduced",
    "acquired",
    "merged",
]


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_entities(text: str) -> Dict:

    result = {
        "subject": "",
        "relation": "",
        "object": "",
        "claim": clean(text),
    }

    lower = text.lower()

    for relation in RELATIONS:

        pattern = rf"\b{re.escape(relation)}\b"

        match = re.search(pattern, lower)

        if match:

            idx = match.start()

            result["subject"] = clean(text[:idx])

            result["relation"] = relation

            result["object"] = clean(
                text[idx + len(relation):]
            )

            break

    return result