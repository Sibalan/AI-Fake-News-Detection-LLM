from typing import List, Dict
from evidence_engine.query_generator import generate_queries

from news_ingest import (
    fetch_newsapi_articles,
    fetch_gnews_articles,
    fetch_newsdata_articles,
    fetch_rss_feed,
    get_all_trusted_feeds,
)


def fetch_evidence(query: str, max_articles: int = 20):

    queries = generate_queries(query)

    evidence = []

    print("\nGenerated Queries:")

    for q in queries:
        print("-", q)

        # -----------------------------
        # NewsAPI
        # -----------------------------
        try:
            evidence.extend(
                fetch_newsapi_articles(
                    q,
                    max_articles=max_articles,
                )
            )
        except Exception as e:
            print("NewsAPI Error:", e)

        # -----------------------------
        # GNews
        # -----------------------------
        try:
            evidence.extend(
                fetch_gnews_articles(
                    q,
                    max_articles=max_articles,
                )
            )
        except Exception as e:
            print("GNews Error:", e)

        # -----------------------------
        # NewsData
        # -----------------------------
        try:
            evidence.extend(
                fetch_newsdata_articles(
                    q,
                    max_articles=max_articles,
                )
            )
        except Exception as e:
            print("NewsData Error:", e)

   
    # -----------------------------
    # RSS
    # -----------------------------
    try:
        for feed in get_all_trusted_feeds():
            evidence.extend(
                fetch_rss_feed(
                    feed,
                    max_items=5,
                )
            )
    except Exception as e:
        print("RSS Error:", e)

    return evidence