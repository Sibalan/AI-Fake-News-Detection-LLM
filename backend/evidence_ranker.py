from typing import Dict, List

SOURCE_WEIGHTS = {

    # Official Sources
    "PIB": 100,
    "Election Commission": 100,
    "Supreme Court": 100,
    "RBI": 100,
    "WHO": 100,
    "CDC": 100,
    "NASA": 100,
    "ISRO": 100,

    # International Trusted Media
    "Reuters": 95,
    "Associated Press": 95,
    "AP": 95,
    "BBC": 95,

    # Indian Trusted Media
    "The Hindu": 92,
    "Indian Express": 92,
    "NDTV": 90,
    "India Today": 90,
    "Hindustan Times": 88,
    "Times of India": 85,

    # AI
    "Knowledge Base": 90,
    "Google Fact Check": 90,
    "Semantic Search": 85,

    # LLM
    "Groq": 75,
    "Ollama": 70,

    # Default
    "NewsAPI": 80,
    "Heuristic": 40,
}


def calculate_evidence_score(evidence_list: List[Dict]) -> Dict:

    real_score = 0
    fake_score = 0

    real_sources = []
    fake_sources = []

    for evidence in evidence_list:

        source = evidence.get("source", "")

        verdict = evidence.get("verdict", "").upper()

        weight = SOURCE_WEIGHTS.get(source, 50)

        # SUPPORT means REAL
        if verdict in ("REAL", "SUPPORT", "SUPPORTS"):

            real_score += weight
            real_sources.append(source)

        # CONTRADICT means FAKE
        elif verdict in ("FAKE", "CONTRADICT", "CONTRADICTS"):

            fake_score += weight
            fake_sources.append(source)

        # Ignore irrelevant evidence
        elif verdict == "IRRELEVANT":
            continue

    return {
        "real_score": real_score,
        "fake_score": fake_score,
        "real_sources": real_sources,
        "fake_sources": fake_sources,
    }