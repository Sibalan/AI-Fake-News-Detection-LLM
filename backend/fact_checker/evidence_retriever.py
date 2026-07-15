import os
import sys


# Allow importing backend modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from news_ingest import (
    fetch_newsapi_articles,
)

from verification_v2.evidence_fetcher import fetch_evidence
from verification_v2.evidence_ranker import rank_articles


def retrieve_evidence(claim, top_k=5):
    """
    Retrieve evidence for the claim.
    """

    subject = claim.get("subject", "").strip()

    # Search only using the subject
    query = f'"{subject}"'

    print(f"\nSearching for: {query}\n")

    evidence = []

    # ---------------------------
    # NewsAPI
    # ---------------------------
    print("Starting NewsAPI...")

    try:
        news = fetch_newsapi_articles(query, max_articles=top_k)

        print("NewsAPI finished")

        for article in news:
            evidence.append(
                {
                    "title": article.get("title", ""),
                    "summary": article.get("description", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", ""),
                    "type": "newsapi",
                }
            )

    except Exception as e:
        print("NewsAPI Error:", e)

    # ---------------------------
    # Semantic Search
    # ---------------------------
    print("Starting Semantic Search...")

    # ---------------------------
    # Unified Evidence Engine
    # ---------------------------
    try:
        queries = [query]

        articles = fetch_evidence(
            queries,
            max_articles=top_k,
        )

        print(f"Fetched {len(articles)} evidence articles")

        ranked_articles = rank_articles(
            query,
            articles,
            top_k=top_k,
        )

        for article in ranked_articles[:top_k]:
            evidence.append(
                {
                    "title": article.get("title", ""),
                    "summary": article.get("description", article.get("summary", "")),
                    "source": article.get("source", ""),
                    "url": article.get("url", article.get("article_url", "")),
                    "published": article.get("published", article.get("published_at", "")),
                    "score": article.get("final_score", 0),
                    "type": "evidence_engine",
                }
            )

    except Exception as e:
        print("Evidence Engine Error:", e)

    return evidence