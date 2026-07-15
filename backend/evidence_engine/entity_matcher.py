import re


STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were",
    "of", "in", "on", "to", "for", "and", "or"
}


def extract_entities(text: str):
    """
    Very lightweight entity extraction.
    Finds capitalized words and multi-word names.
    """

    if not text:
        return set()

    entities = set()

    pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"

    for match in re.findall(pattern, text):
        name = match.strip()

        if name.lower() not in STOPWORDS:
            entities.add(name.lower())

    return entities


def entity_match_score(claim: str, article: str):

    claim_entities = extract_entities(claim)

    article_entities = extract_entities(article)

    if not claim_entities:
        return 0.0

    common = claim_entities & article_entities

    return round(
        len(common) / len(claim_entities),
        2
    )