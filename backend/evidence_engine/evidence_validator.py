import re
from difflib import SequenceMatcher


NEGATIVE_WORDS = {
    "false",
    "fake",
    "hoax",
    "misleading",
    "incorrect",
    "denied",
    "refuted",
    "debunked",
    "fabricated",
    "rumour",
    "rumor",
    "not true"
}


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        (a or "").lower(),
        (b or "").lower()
    ).ratio()


def validate_evidence(claim: str, article: dict):

    title = article.get("title", "")
    summary = article.get("summary", "")

    text = f"{title} {summary}".lower()

    # Strong contradiction words
    for word in NEGATIVE_WORDS:
        if word in text:
            return "CONTRADICT"

    score = max(

        similarity(claim, title),

        similarity(claim, summary)

    )

    if score >= 0.75:
        return "SUPPORT"

    if score >= 0.45:
        return "PARTIAL"

    return "IRRELEVANT"