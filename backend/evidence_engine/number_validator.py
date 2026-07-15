import re


def extract_numbers(text: str):
    """
    Extract integers, decimals and percentages from text.
    """

    if not text:
        return []

    pattern = r"\d+(?:\.\d+)?%?"

    return re.findall(pattern, text)


def number_match_score(claim: str, article: str):
    """
    Returns a score between 0 and 1.

    1.0 = all numbers match
    0.0 = no numbers match
    """

    claim_numbers = extract_numbers(claim)

    article_numbers = extract_numbers(article)

    if not claim_numbers:
        return 1.0

    matched = 0

    for number in claim_numbers:
        if number in article_numbers:
            matched += 1

    return round(matched / len(claim_numbers), 2)