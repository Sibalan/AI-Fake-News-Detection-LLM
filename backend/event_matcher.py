from reasoning.fact_comparator import compare_facts
from difflib import SequenceMatcher
import re


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


NEGATIVE_WORDS = {
    "false",
    "fake",
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
}


def event_match(claim, article):
    claim = normalize(claim)
    article = normalize(article)

    # -----------------------------
    # Fact-based reasoning
    # -----------------------------
    fact_result = compare_facts(claim, article)

    if fact_result == "SUPPORT":
        return "SUPPORT", 1.0

    if fact_result == "CONTRADICT":
        return "CONTRADICT", 1.0

    similarity = SequenceMatcher(None, claim, article).ratio()

    claim_words = set(claim.split())
    article_words = set(article.split())

    common = claim_words & article_words

    # Explicit contradiction only if article itself says the claim is false
    for word in NEGATIVE_WORDS:
        if word in article:
            return "CONTRADICT", round(similarity, 2)

    # Strong support
    if similarity >= 0.75:
        return "SUPPORT", round(similarity, 2)

    if len(common) >= 5:
        return "SUPPORT", round(similarity, 2)

    # Partial support (stricter)
    if similarity >= 0.60 and len(common) >= 5:
        return "PARTIAL", round(similarity, 2)

    # Low similarity does NOT mean contradiction
    return "IRRELEVANT", round(similarity, 2)