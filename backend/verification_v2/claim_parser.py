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
    "signed",
    "approved",
    "declared",
]


QUESTION_WORDS = {
    "did",
    "does",
    "do",
    "is",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "can",
    "could",
    "will",
    "would",
}


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_claim(text: str) -> Dict:

    original = clean(text)

    words = original.split()

    if words and words[0].lower() in QUESTION_WORDS:
        normalized = " ".join(words[1:])
    else:
        normalized = original

    result = {
        "original": original,
        "normalized": normalized,
        "subject": "",
        "relation": "",
        "object": "",
    }

    lower = normalized.lower()

    for relation in RELATIONS:

        pattern = rf"\b{re.escape(relation)}\b"

        match = re.search(pattern, lower)

        if match:

            idx = match.start()

            result["subject"] = clean(normalized[:idx])

            result["relation"] = relation

            result["object"] = clean(
                normalized[idx + len(relation):]
            )

            break

    return result