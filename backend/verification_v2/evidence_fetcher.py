from typing import List, Dict

from news_ingest import (
    fetch_newsapi_articles,
    fetch_gnews_articles,
    fetch_newsdata_articles,
    fetch_rss_feed,
    get_all_trusted_feeds,
)

from verification_v2.normalizer import normalize_article
from verification_v2.query_expander import expand_queries


def fetch_evidence(
    queries: List[str],
    max_articles: int = 20,
) -> List[Dict]:

    queries = expand_queries(queries)

    articles = []

    for query in queries:
        try:
            articles.extend(
                fetch_newsapi_articles(
                    query,
                    max_articles=max_articles,
                )
            )
        except Exception as e:
            print("NewsAPI:", e)

        try:
            articles.extend(
                fetch_gnews_articles(
                    query,
                    max_articles=max_articles,
                )
            )
        except Exception as e:
            print("GNews:", e)

        try:
            articles.extend(
                fetch_newsdata_articles(
                    query,
                    max_articles=max_articles,
                )
            )
        except Exception as e:
            print("NewsData:", e)

    # Fetch from RSS feeds
    try:
        for feed in get_all_trusted_feeds():
            articles.extend(
                fetch_rss_feed(
                    feed,
                    max_items=10,
                )
            )
    except Exception as e:
        print("RSS:", e)

    normalized_articles = []
    for article in articles:
        try:
            normalized_articles.append(
                normalize_article(article)
            )
        except Exception:
            pass

    unique_articles = []
    seen_urls = set()

    for article in normalized_articles:
        url = article.get("url", "").strip()
        if not url:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_articles.append(article)

    return unique_articles