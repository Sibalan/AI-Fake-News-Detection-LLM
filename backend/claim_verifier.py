import re


ROLE_MAP = {
    "prime minister": "Prime Minister",
    "president": "President",
    "chief minister": "Chief Minister",
    "governor": "Governor",
    "ceo": "CEO",
    "founder": "Founder",
    "captain": "Captain",
}


def extract_names(text: str):
    """
    Extract simple person names (2 or more consecutive capitalized words).
    """
    return set(
        re.findall(
            r"\b[A-Z][a-zA-Z.]+(?:\s+[A-Z][a-zA-Z.]+)+",
            text,
        )
    )


def extract_roles(text: str):
    """
    Extract roles from text.
    """
    text = text.lower()

    roles = []

    for key, value in ROLE_MAP.items():
        if key in text:
            roles.append(value)

    return roles


def verify_roles(claim: str, article: str):
    """
    Returns:
        SUPPORT
        CONTRADICT
        UNKNOWN
    """

    claim_roles = set(extract_roles(claim))
    article_roles = set(extract_roles(article))

    if not claim_roles or not article_roles:
        return "UNKNOWN"

    # Different roles mentioned
    if not (claim_roles & article_roles):
        return "UNKNOWN"

    claim_names = extract_names(claim)
    article_names = extract_names(article)

    # If we couldn't detect names, don't guess
    if not claim_names or not article_names:
        return "UNKNOWN"

    # Same role + same person
    if claim_names & article_names:
        return "SUPPORT"

    # Same role but different person
    return "CONTRADICT"