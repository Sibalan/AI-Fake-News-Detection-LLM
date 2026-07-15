from reasoning.fact_extractor import extract_fact


SPORT_KEYWORDS = {
    "football": [
        "football",
        "fifa",
        "world cup",
        "soccer",
        "uefa",
        "champions league",
        "premier league",
    ],
    "cricket": [
        "cricket",
        "ipl",
        "odi",
        "t20",
        "bcci",
        "icc",
        "test match",
    ],
}


def detect_domain(text: str):
    """
    Detect the domain/topic of the object.
    Example:
        football player -> football
        FIFA World Cup -> football
        IPL -> cricket
    """
    text = text.lower()

    for domain, words in SPORT_KEYWORDS.items():
        for word in words:
            if word in text:
                return domain

    return None


def compare_facts(claim: str, evidence: str):
    """
    Compare a claim against evidence.

    Returns:
        SUPPORT
        CONTRADICT
        IRRELEVANT
    """

    claim_fact = extract_fact(claim)
    evidence_fact = extract_fact(evidence)

    claim_subject = claim_fact["subject"].lower()
    evidence_subject = evidence_fact["subject"].lower()

    # Subjects don't match
    if claim_subject and evidence_subject:
        if claim_subject not in evidence_subject and evidence_subject not in claim_subject:
            return "IRRELEVANT"

    claim_domain = detect_domain(claim_fact["object"])
    evidence_domain = detect_domain(evidence)

    if claim_domain and evidence_domain:

        if claim_domain == evidence_domain:
            return "SUPPORT"

        return "CONTRADICT"

    return "IRRELEVANT"