from difflib import SequenceMatcher
import re

NEGATIVE_WORDS = {
    "fake",
    "false",
    "hoax",
    "misleading",
    "incorrect",
    "debunked",
    "denied",
    "refuted",
    "fabricated",
    "rumour",
    "rumor",
    "not true",
    "never happened",
}

POSITIVE_WORDS = {
    "confirmed",
    "official",
    "announced",
    "declared",
    "won",
    "appointed",
    "elected",
    "approved",
    "launched",
    "signed",
}


def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def verify_evidence(claim: str, article: dict):

    title = article.get("title", "")
    summary = article.get("summary", "")

    evidence = normalize(title + " " + summary)
    claim = normalize(claim)

    similarity = SequenceMatcher(
        None,
        claim,
        evidence
    ).ratio()

    # Explicit contradiction
    for word in NEGATIVE_WORDS:
        if word in evidence:
            return {
                "verdict": "CONTRADICT",
                "confidence": 95,
            }

    # Strong support
    if similarity >= 0.75:
        return {
            "verdict": "SUPPORT",
            "confidence": 95,
        }

    # Medium support
    if similarity >= 0.50:
        return {
            "verdict": "PARTIAL",
            "confidence": 75,
        }

    return {
        "verdict": "IRRELEVANT",
        "confidence": 40,
    }