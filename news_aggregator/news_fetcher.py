import logging
import requests
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

TRUSTED_SOURCES = [
    "bbc-news",
    "cnn",
    "the-verge",
    "reuters",
    "the-hindu",
    "the-washington-post",
    "al-jazeera-english",
    "financial-times",
    "business-insider",
    "bloomberg",
]

CATEGORY_MAP = {
    "latest": {"query": "breaking OR latest", "api_category": None},
    "sports": {"query": "sports", "api_category": "sports"},
    "international-relations": {
        "query": "international relations OR diplomacy OR foreign policy",
        "api_category": None,
    },
    "general-knowledge": {"query": "general knowledge OR facts OR trivia", "api_category": None},
    "science-technology": {"query": "science OR technology OR innovation", "api_category": None},
    "indian-polity": {"query": "Indian polity OR Indian politics OR constitution", "api_category": None},
    "finance-economy": {
        "query": "finance OR economy OR economic policy",
        "api_category": None,
    },
    "business": {"query": "business", "api_category": "business"},
    "entertainment": {"query": "entertainment OR movies OR music", "api_category": "entertainment"},
}

CATEGORY_LABELS = {
    "latest": "Latest News",
    "sports": "Sports",
    "international-relations": "International Relations",
    "general-knowledge": "General Knowledge",
    "science-technology": "Science & Technology",
    "indian-polity": "Indian Polity",
    "finance-economy": "Finance & Economy",
    "business": "Business",
    "entertainment": "Entertainment",
}

class NewsFetcher:
    def __init__(self, config, llm_client=None):
        self.newsapi_key = config.NEWSAPI_KEY
        self.gnews_key = config.GNEWS_API_KEY
        self.guardian_key = config.GUARDIAN_API_KEY
        self.llm_client = llm_client

    def fetch_latest(self, trusted_only: bool = False) -> List[Dict]:
        return self.fetch_by_category("latest", trusted_only=trusted_only)

    def fetch_trusted(self) -> List[Dict]:
        return self.fetch_by_category("latest", trusted_only=True)

    def fetch_by_category(self, category_slug: str, trusted_only: bool = False) -> List[Dict]:
        category_slug = category_slug.lower()
        category = CATEGORY_MAP.get(category_slug, CATEGORY_MAP["general-knowledge"])
        articles = []

        if self.newsapi_key:
            sources = TRUSTED_SOURCES if trusted_only else None
            articles += self._fetch_newsapi(category["query"], category["api_category"], sources=sources)
        if self.gnews_key:
            articles += self._fetch_gnews(category["query"], trusted_only=trusted_only)
        if self.guardian_key and category_slug != "latest":
            articles += self._fetch_guardian(category["query"])

        articles = self._dedupe_articles(articles)
        return self._enrich_articles(articles, category_slug, trusted_only=trusted_only)

    def search(self, query: str) -> List[Dict]:
        query = query.strip()
        if not query:
            return []

        articles = []
        if self.newsapi_key:
            articles += self._fetch_newsapi(query, None)
        if self.gnews_key:
            articles += self._fetch_gnews(query)
        if self.guardian_key:
            articles += self._fetch_guardian(query)

        articles = self._dedupe_articles(articles)
        return self._enrich_articles(articles, "general-knowledge")

    def _fetch_newsapi(self, query: str, api_category: str = None, sources: list = None) -> List[Dict]:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": self.newsapi_key,
            "pageSize": 25,
            "language": "en",
        }
        if sources:
            params["sources"] = ",".join(sources)
        elif api_category:
            params["category"] = api_category
        else:
            params["q"] = query
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            return [self._normalize_newsapi_article(item) for item in articles]
        except Exception as ex:
            logger.warning(f"NewsAPI fetch failed: {ex}")
            return []

    def _fetch_gnews(self, query: str, trusted_only: bool = False) -> List[Dict]:
        url = "https://gnews.io/api/v4/search"
        params = {
            "token": self.gnews_key,
            "q": query,
            "lang": "en",
            "max": 20,
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            normalized = [self._normalize_gnews_article(item) for item in articles]
            if trusted_only:
                normalized = [item for item in normalized if self._is_trusted_source(item.get("source"))]
            return normalized
        except Exception as ex:
            logger.warning(f"GNews fetch failed: {ex}")
            return []

    def _fetch_guardian(self, query: str) -> List[Dict]:
        url = "https://content.guardianapis.com/search"
        params = {
            "api-key": self.guardian_key,
            "q": query,
            "show-fields": "headline,trailText,body,thumbnail",
            "page-size": 15,
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            results = data.get("response", {}).get("results", [])
            return [self._normalize_guardian_article(item) for item in results]
        except Exception as ex:
            logger.warning(f"Guardian fetch failed: {ex}")
            return []

    def _normalize_newsapi_article(self, item: Dict) -> Dict:
        return {
            "title": item.get("title") or item.get("description") or "Untitled",
            "description": item.get("description", ""),
            "content": item.get("content", ""),
            "url": item.get("url"),
            "image_url": item.get("urlToImage"),
            "source": item.get("source", {}).get("name", "NewsAPI"),
            "published_at": item.get("publishedAt"),
        }

    def _normalize_gnews_article(self, item: Dict) -> Dict:
        return {
            "title": item.get("title") or item.get("description") or "Untitled",
            "description": item.get("description", ""),
            "content": item.get("content", ""),
            "url": item.get("url"),
            "image_url": item.get("image"),
            "source": item.get("source", {}).get("name", "GNews"),
            "published_at": item.get("publishedAt"),
        }

    def _normalize_guardian_article(self, item: Dict) -> Dict:
        fields = item.get("fields", {})
        return {
            "title": fields.get("headline") or item.get("webTitle") or "Untitled",
            "description": fields.get("trailText", ""),
            "content": fields.get("body", ""),
            "url": item.get("webUrl"),
            "image_url": fields.get("thumbnail"),
            "source": "The Guardian",
            "published_at": item.get("webPublicationDate"),
        }

    def _is_trusted_source(self, source_name: str) -> bool:
        if not source_name:
            return False
        normalized = source_name.strip().lower().replace(" ", "").replace(".", "").replace("&", "and")
        for trusted in TRUSTED_SOURCES:
            trusted_normalized = trusted.lower().replace("-", "").replace(" ", "").replace(".", "").replace("&", "and")
            if trusted_normalized in normalized or normalized in trusted_normalized:
                return True
        return "guardian" in normalized

    def _dedupe_articles(self, articles: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for article in articles:
            key = (article.get("url"), article.get("title", "").strip().lower())
            if key in seen or not article.get("url"):
                continue
            seen.add(key)
            unique.append(article)
        return unique

    def _enrich_articles(self, articles: List[Dict], category_slug: str, trusted_only: bool = False) -> List[Dict]:
        enriched = []
        for item in articles[:30]:
            title = item.get("title", "Untitled")
            description = item.get("description", "")
            content = item.get("content", "") or description
            source = item.get("source", "Unknown")
            summary = description or content[:250]
            category_label = CATEGORY_LABELS.get(category_slug, "General Knowledge")
            credibility_score = 70.0
            suspicious_reason = ""
            headline = title
            trusted = self._is_trusted_source(source)

            if self.llm_client:
                analysis = self.llm_client.analyze_article(title, description, content, source)
                summary = analysis.get("summary", summary)
                category_label = analysis.get("category", category_label)
                credibility_score = analysis.get("credibility_score", credibility_score)
                suspicious_reason = analysis.get("suspicious_reason", "")
                headline = analysis.get("headline", title)

            enriched.append(
                {
                    "title": headline,
                    "original_title": title,
                    "description": summary,
                    "content": content,
                    "url": item.get("url"),
                    "image_url": item.get("image_url"),
                    "source": source,
                    "category": category_label,
                    "published_at": item.get("published_at"),
                    "credibility_score": credibility_score,
                    "suspicious_reason": suspicious_reason,
                    "trusted_source": trusted,
                    "latest": category_slug == "latest",
                }
            )
        return enriched
