import re
from typing import Dict


RELATIONS = [
    "is",
    "was",
    "are",
    "were",
    "won",
    "beat",
    "defeated",
    "appointed",
    "elected",
    "became",
    "launched",
    "announced",
    "introduced",
    "acquired",
    "merged",
    "joined",
    "resigned",
    "died",
    "killed",
    "arrested",
]


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_fact(sentence: str) -> Dict:
    """
    Extract:
        Subject
        Relation
        Object

    Example:
        Messi is a football player

    Returns:

    {
        "subject": "Messi",
        "relation": "is",
        "object": "a football player"
    }
    """

    sentence = clean(sentence)

    result = {
        "subject": "",
        "relation": "",
        "object": "",
        "original": sentence,
    }

    lower = sentence.lower()

    for relation in RELATIONS:

        pattern = rf"\b{re.escape(relation)}\b"

        match = re.search(pattern, lower)

        if match:

            start = match.start()

            result["subject"] = clean(sentence[:start])

            result["relation"] = relation

            result["object"] = clean(
                sentence[start + len(relation):]
            )

            break

    return result