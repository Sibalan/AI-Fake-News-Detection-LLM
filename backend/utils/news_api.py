import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_TOP_HEADLINES = "https://newsapi.org/v2/top-headlines"
NEWS_API_EVERYTHING = "https://newsapi.org/v2/everything"
MAX_ARTICLES = 12
REQUEST_TIMEOUT = 12

# category → API config (no 'sources' mixed with country/category — causes 0 results)
CATEGORY_MAP = {
    "breaking": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "general", "country": "us", "pageSize": 10},
    },
    "world": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "general", "country": "us"},
    },
    "india": {
        "endpoint": NEWS_API_EVERYTHING,
        "params": {
            "q": "india",
            "language": "en",
            "sortBy": "publishedAt",
        },
    },
    "indian politics": {
        "endpoint": NEWS_API_EVERYTHING,
        "params": {
            "q": "india politics OR lok sabha OR rajya sabha OR BJP OR congress OR modi OR chief minister india",
            "language": "en",
            "sortBy": "publishedAt",
        },
    },
    "sports": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "sports", "country": "us"},
    },
    "technology": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "technology", "country": "us"},
    },
    "science": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "science", "country": "us"},
    },
    "health": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "health", "country": "us"},
    },
    "finance": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "business", "country": "us"},
    },
    "entertainment": {
        "endpoint": NEWS_API_TOP_HEADLINES,
        "params": {"category": "entertainment", "country": "us"},
    },
    "education": {
        "endpoint": NEWS_API_EVERYTHING,
        "params": {
            "q": "education schools universities students",
            "language": "en",
            "sortBy": "publishedAt",
        },
    },
    "international": {
        "endpoint": NEWS_API_EVERYTHING,
        "params": {
            "q": "international world global",
            "language": "en",
            "sortBy": "publishedAt",
        },
    },
}

DEFAULT_PARAMS = {
    "pageSize": MAX_ARTICLES,
}


class NewsApiError(Exception):
    pass


def _normalize_category(category: str) -> str:
    if not category:
        return "world"
    text = category.strip().lower()
    aliases = {
        "politics": "indian politics",
        "political": "indian politics",
        "india politics": "indian politics",
        "business": "finance",
        "tech": "technology",
        "sci": "science",
        "entertain": "entertainment",
        "edu": "education",
        "global": "international",
        "general": "world",
    }
    return aliases.get(text, text)


def _format_published(dt_str: Optional[str]) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "just now"
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 7:
            return f"{days}d ago"
        return dt.strftime("%b %d")
    except Exception:
        return ""


def fetch_latest_news(category: str, max_articles: int = MAX_ARTICLES) -> List[Dict]:
    if not NEWS_API_KEY:
        raise NewsApiError("NEWS_API_KEY is not configured")

    normalized = _normalize_category(category)
    config = CATEGORY_MAP.get(normalized, CATEGORY_MAP["world"])
    endpoint = config["endpoint"]
    params = {**DEFAULT_PARAMS, **config["params"], "apiKey": NEWS_API_KEY}
    params["pageSize"] = max_articles

    # top-headlines doesn't support sortBy or language alongside country/category
    if endpoint == NEWS_API_TOP_HEADLINES:
        params.pop("sortBy", None)
        params.pop("language", None)

    try:
        response = requests.get(endpoint, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        logger.warning(f"NewsAPI request failed: {exc}")
        raise NewsApiError("Unable to fetch news") from exc

    if payload.get("status") != "ok":
        msg = payload.get("message", "Unable to fetch news")
        logger.warning(f"NewsAPI error for '{category}': {msg}")
        raise NewsApiError(msg)

    articles = []
    for item in payload.get("articles", [])[:max_articles]:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        if not title or not url or "[Removed]" in title:
            continue

        description = (item.get("description") or "").strip()
        content = (item.get("content") or "").strip()
        image_url = (item.get("urlToImage") or "").strip()
        source_name = (item.get("source", {}) or {}).get("name", "") or ""
        published_raw = item.get("publishedAt", "")

        articles.append({
            "title": title,
            "description": description or (content[:200] if content else ""),
            "url": url,
            "image_url": image_url,
            "source": source_name,
            "published": _format_published(published_raw),
            "published_raw": published_raw,
        })

    if not articles:
        raise NewsApiError(f"No articles returned for '{category}'")

    return articles


def fetch_breaking_news(max_articles: int = 8) -> List[Dict]:
    return fetch_latest_news("breaking", max_articles=max_articles)
