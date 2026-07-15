from datetime import datetime
from difflib import SequenceMatcher


TRUST_SCORES = {

    "Reuters": 100,
    "Associated Press": 98,
    "AP News": 98,
    "BBC": 97,
    "Press Trust of India": 96,
    "PTI": 96,
    "The Hindu": 95,
    "Indian Express": 94,
    "PIB": 95,
    "WHO": 100,
    "NASA": 100,
    "ISRO": 99,
    "ICC": 98,
    "FIFA": 98,

}


def similarity(a, b):

    return SequenceMatcher(
        None,
        a.lower(),
        b.lower()
    ).ratio()


def rank_evidence(claim, articles):

    ranked = []

    for article in articles:

        title = article.get("title", "")
        summary = article.get("summary", "")
        source = article.get("source", "Unknown")

        relevance = max(

            similarity(claim, title),

            similarity(claim, summary)

        )

        credibility = TRUST_SCORES.get(source, 70)

        final_score = (

            relevance * 70

            +

            credibility * 0.30

        )

        article["relevance"] = round(relevance * 100, 2)

        article["credibility"] = credibility

        article["final_score"] = round(final_score, 2)

        ranked.append(article)

    ranked.sort(

        key=lambda x: x["final_score"],

        reverse=True

    )

    return ranked