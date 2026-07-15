from verification_v2.evidence_ranker import rank_articles

claim = "Chief Minister of Tamil Nadu is M. K. Stalin"

articles = [
    {
        "title": "M. K. Stalin inaugurated a new bridge in Chennai",
        "summary": "The Chief Minister of Tamil Nadu attended the event.",
        "content": "",
        "source": "The Hindu",
    },
    {
        "title": "Virat Kohli scored a century",
        "summary": "RCB won the match.",
        "content": "",
        "source": "ESPN",
    },
    {
        "title": "Heavy rainfall expected in Kerala",
        "summary": "IMD issued an alert.",
        "content": "",
        "source": "IMD",
    },
]

results = rank_articles(claim, articles)

print("\n===== Semantic Ranking =====\n")

for article in results:
    print(article["semantic_score"], "-", article["title"])