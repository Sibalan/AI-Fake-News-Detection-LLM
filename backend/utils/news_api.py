import os
import logging
from typing import List, Dict

import requests

logger = logging.getLogger(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_TOP_HEADLINES = "https://newsapi.org/v2/top-headlines"
NEWS_API_EVERYTHING = "https://newsapi.org/v2/everything"
MAX_ARTICLES = 4
REQUEST_TIMEOUT = 10

CATEGORY_MAP = {
    "sports": {"endpoint": NEWS_API_TOP_HEADLINES, "params": {"category": "sports"}},
    "finance": {"endpoint": NEWS_API_TOP_HEADLINES, "params": {"category": "business"}},
    "education": {"endpoint": NEWS_API_EVERYTHING, "params": {"q": "education OR schools OR universities"}},
    "health": {"endpoint": NEWS_API_TOP_HEADLINES, "params": {"category": "health"}},
    "international": {"endpoint": NEWS_API_EVERYTHING, "params": {"q": "international OR world news"}},
    "indian politics": {
        "endpoint": NEWS_API_EVERYTHING,
        "params": {"q": "india politics OR indian politics OR lok sabha OR rajya sabha OR bharatiya janata party OR congress"},
    },
}

DEFAULT_PARAMS = {
    "language": "en",
    "pageSize": MAX_ARTICLES,
    "sortBy": "publishedAt",
}


class NewsApiError(Exception):
    pass


def _normalize_category(category: str) -> str:
    if not category:
        return "international"
    text = category.strip().lower()
    if text in ("politics", "political", "indian politics", "india politics", "india politics"):
        return "indian politics"
    return text


def fetch_latest_news(category: str) -> List[Dict[str, str]]:
    if not NEWS_API_KEY:
        raise NewsApiError("NEWS_API_KEY is not configured")

    normalized = _normalize_category(category)
    config = CATEGORY_MAP.get(normalized, CATEGORY_MAP["international"])
    endpoint = config["endpoint"]
    params = {**DEFAULT_PARAMS, **config["params"], "apiKey": NEWS_API_KEY}

    if endpoint == NEWS_API_TOP_HEADLINES:
        params.pop("sortBy", None)

    try:
        response = requests.get(endpoint, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        logger.warning(f"NewsAPI request failed: {exc}")
        raise NewsApiError("Unable to fetch news") from exc

    if payload.get("status") != "ok":
        logger.warning("NewsAPI returned unexpected status: %s", payload)
        raise NewsApiError("Unable to fetch news")

    articles = []
    for item in payload.get("articles", [])[:MAX_ARTICLES]:
        title = (item.get("title") or "").strip()
        description = (item.get("description") or item.get("content") or "").strip()
        url = (item.get("url") or "").strip()
        if not title or not url:
            continue
        articles.append({
            "title": title,
            "description": description,
            "url": url,
        })

    if not articles:
        raise NewsApiError("No articles returned")

    return articles
