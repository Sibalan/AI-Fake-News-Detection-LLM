MEDIASTACK_ENDPOINT = "http://api.mediastack.com/v1/news"
NEWSAPI_RATE_LIMITED = False
import os
import logging
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

# qdrant imports are optional and performed lazily to allow running the app
# without a local Qdrant service or Docker. Use the `QDRANT_ENABLED` flag in
# `backend/config.py` to enable vector features.

from backend.config import Config
from backend.models.live_article import LiveArticle
from backend.models import db

logger = logging.getLogger(__name__)

RSS_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
}

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_EMBEDDING_MODEL = None
_QDRANT = None
# Start Qdrant availability based on config flag (default: disabled)
_QDRANT_AVAILABLE = Config.QDRANT_ENABLED
_QDRANT_ERROR_LOGGED = False
_RSS_FEED_ERRORS_LOGGED = set()
COLLECTION_NAME = Config.QDRANT_COLLECTION
TRUSTED_SOURCE_QUERY = (
    "Reuters OR BBC OR Associated Press OR The Guardian OR CNN OR Al Jazeera OR "
    "Hindustan Times OR Indian Express OR NDTV OR Times of India OR ANI OR PIB OR NPR"
)

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"
GNEWS_ENDPOINT = "https://gnews.io/api/v4/search"
NEWSDATA_ENDPOINT = "https://newsdata.io/api/1/news"
MEDIASTACK_ENDPOINT = "http://api.mediastack.com/v1/news"


def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
    return _EMBEDDING_MODEL


def get_qdrant_client() -> Optional[object]:
    global _QDRANT, _QDRANT_AVAILABLE, rest, _QDRANT_ERROR_LOGGED
    # If Qdrant feature disabled via config, skip any attempts
    if not Config.QDRANT_ENABLED:
        _QDRANT_AVAILABLE = False
        return None

    if not _QDRANT_AVAILABLE:
        return None

    # Lazy import to avoid import-time failures when the package isn't installed
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as rest_mod
        rest = rest_mod
    except Exception as exc:
        if not _QDRANT_ERROR_LOGGED:
            logger.warning(f"qdrant-client package not available: {exc}")
            _QDRANT_ERROR_LOGGED = True
        _QDRANT_AVAILABLE = False
        return None

    if _QDRANT is None:
        try:
            _QDRANT = QdrantClient(
                url=f"http://{Config.QDRANT_HOST}:{Config.QDRANT_PORT}",
                api_key=Config.QDRANT_API_KEY or None,
            )
        except Exception as exc:
            if not _QDRANT_ERROR_LOGGED:
                logger.warning(f"Qdrant connection failed: {exc}")
                _QDRANT_ERROR_LOGGED = True
            _QDRANT = None
            _QDRANT_AVAILABLE = False
    return _QDRANT


def ensure_qdrant_collection() -> bool:
    try:
        client = get_qdrant_client()
        if client is None:
            return False
        try:
            collection = client.get_collection(collection_name=COLLECTION_NAME)
        except Exception:
            collection = None

        if not collection:
            client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=rest.VectorParams(
                    size=get_embedding_model().get_sentence_embedding_dimension(),
                    distance=rest.Distance.COSINE,
                ),
                optimizers_config=rest.OptimizersConfig(
                    default_segment_number=1,
                    flush_interval_sec=1,
                ),
            )
        return True
    except Exception as exc:
        global _QDRANT_AVAILABLE, _QDRANT_ERROR_LOGGED
        if not _QDRANT_ERROR_LOGGED:
            logger.warning(f"Unable to initialize Qdrant collection: {exc}")
            _QDRANT_ERROR_LOGGED = True
        _QDRANT_AVAILABLE = False
        return False


def _normalize_article(article: Dict) -> Dict:
    source_value = article.get("source")
    if isinstance(source_value, dict):
        source_value = source_value.get("name") or source_value.get("title") or ""

    link = article.get("url") or article.get("link") or ""
    source_domain = article.get("source_domain") or article.get("source_domain") or ""
    if not source_domain and link:
        try:
            source_domain = urlparse(link).netloc
        except Exception:
            source_domain = ""

    return {
        "title": (article.get("title") or "")[:500],
        "description": (article.get("description") or article.get("content") or "")[:400],
        "content": article.get("content") or article.get("description") or "",
        "author": article.get("author") or article.get("creator") or "",
        "source": source_value or "",
        "source_domain": source_domain,
        "published_at": article.get("publishedAt") or article.get("pubDate") or article.get("published") or article.get("published_at"),
        "country": article.get("country") or "",
        "language": article.get("language") or "en",
        "category": article.get("category") or "general",
        "keywords": ",".join(article.get("keywords", [])) if article.get("keywords") else "",
        "image_url": article.get("urlToImage") or article.get("image_url") or article.get("image") or "",
        "article_url": link,
    }


def _make_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.fromtimestamp(float(value))
        except Exception:
            return None


def _is_trusted_source(source: str) -> bool:
    if not source:
        return False
    normalized_source = source.lower().replace(" ", "").replace("-", "").replace(".", "")
    for trusted in Config.TRUSTED_SOURCES:
        trusted_normalized = trusted.lower().replace(" ", "").replace("-", "").replace(".", "")
        if trusted_normalized in normalized_source or normalized_source in trusted_normalized:
            return True
    return any(trusted.lower() in source.lower() for trusted in Config.TRUSTED_SOURCES)


def _dedupe_articles(articles: List[Dict]) -> List[Dict]:
    seen = set()
    result = []
    for item in articles:
        url = (item.get("article_url") or "").strip().lower()
        title = (item.get("title") or "").strip().lower()
        if not url:
            continue
        key = (url, title)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _build_embedding_text(article: Dict) -> str:
    parts = [article.get("title", ""), article.get("description", ""), article.get("content", "")]
    text = " . ".join([part.strip() for part in parts if part and part.strip()])
    return text[:3000]


def _get_article_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    if hasattr(vectors, "tolist"):
        return vectors.tolist()
    return [list(vec) for vec in vectors]


def _build_qdrant_payload(article: Dict) -> Dict:
    return {
        "title": article.get("title"),
        "source": article.get("source"),
        "source_domain": article.get("source_domain"),
        "published_at": _make_timestamp(article.get("published_at")).isoformat() if _make_timestamp(article.get("published_at")) else None,
        "trusted_source": _is_trusted_source(article.get("source") or ""),
        "category": article.get("category"),
        "article_url": article.get("article_url"),
        "summary": article.get("description"),
        "source_text": (article.get("content") or "")[:600],
    }


def _save_article(article_data: Dict, vector: Optional[List[float]] = None) -> LiveArticle:
    published_at = _make_timestamp(article_data.get("published_at"))
    existing = LiveArticle.query.filter_by(article_url=article_data["article_url"]).first()
    if existing:
        existing.title = article_data["title"]
        existing.description = article_data["description"]
        existing.content = article_data["content"]
        existing.author = article_data["author"]
        existing.source = article_data["source"]
        existing.source_domain = article_data["source_domain"]
        existing.published_at = published_at
        existing.country = article_data["country"]
        existing.language = article_data["language"]
        existing.category = article_data["category"]
        existing.keywords = article_data["keywords"]
        existing.image_url = article_data["image_url"]
        existing.credibility_score = 90.0 if _is_trusted_source(article_data["source"]) else 70.0
        existing.verification_status = "trusted" if _is_trusted_source(article_data["source"]) else "pending"
        existing.summary = article_data["description"]
        existing.fact_check_status = "unverified"
        record = existing
    else:
        record = LiveArticle(
            title=article_data["title"],
            description=article_data["description"],
            content=article_data["content"],
            author=article_data["author"],
            source=article_data["source"] or "Unknown",
            source_domain=article_data["source_domain"],
            published_at=published_at,
            country=article_data["country"],
            language=article_data["language"],
            category=article_data["category"],
            keywords=article_data["keywords"],
            image_url=article_data["image_url"],
            article_url=article_data["article_url"],
            credibility_score=90.0 if _is_trusted_source(article_data["source"]) else 70.0,
            verification_status="trusted" if _is_trusted_source(article_data["source"]) else "pending",
            summary=article_data["description"],
            fact_check_status="unverified",
        )
        try:
            db.session.add(record)
            db.session.flush()
        except Exception as e:
            db.session.rollback()
            logger.warning(
                f"Duplicate article skipped: {article_data['article_url']} - {e}"
            )
            return None

    record.embedding_id = str(record.id)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Database commit failed: {e}")
        return record

    if vector is not None:
        try:
            if not ensure_qdrant_collection():
                return record
            client = get_qdrant_client()
            if client is None:
                return record
            payload = _build_qdrant_payload(article_data)
            point = rest.PointStruct(
                id=record.embedding_id,
                vector=vector,
                payload=payload,
            )
            client.upsert(collection_name=COLLECTION_NAME, points=[point])
        except Exception as exc:
            logger.warning(f"Qdrant upsert failed for {article_data.get('article_url')}: {exc}")

    return record


def ingest_trusted_news(max_articles: int = 50) -> int:
    logger.info("Starting live news ingestion from trusted sources")
    articles = []
    try:
        articles += fetch_newsapi_articles(TRUSTED_SOURCE_QUERY, max_articles=max_articles)
    except Exception as exc:
        logger.warning(f"NewsAPI trusted ingest failed: {exc}")
    try:
        articles += fetch_gnews_articles(TRUSTED_SOURCE_QUERY, max_articles=max_articles)
    except Exception as exc:
        logger.warning(f"GNews trusted ingest failed: {exc}")
    try:
        articles += fetch_newsdata_articles(TRUSTED_SOURCE_QUERY, max_articles=max_articles)
    except Exception as exc:
        logger.warning(f"NewsData trusted ingest failed: {exc}")

    for feed in get_all_trusted_feeds():
        articles += fetch_rss_feed(feed, max_items=10)

    normalized = [_normalize_article(item) for item in articles]
    normalized = _dedupe_articles(normalized)

    if not normalized:
        logger.warning("Trusted news ingestion found no articles")
        return 0

    saved = 0
    texts = [_build_embedding_text(item) for item in normalized]
    vectors = []
    try:
        vectors = _get_article_embeddings(texts)
    except Exception as exc:
        logger.warning(f"Embedding generation failed: {exc}")

    for idx, item in enumerate(normalized):
        if not item.get("article_url"):
            continue
        vector = vectors[idx] if idx < len(vectors) else None
        try:
            record = _save_article(item, vector=vector)
            if record:
                saved += 1
        except Exception as exc:
            logger.warning(f"Failed to save live article {item.get('article_url')}: {exc}")

    logger.info(f"Live news ingestion complete: {saved} articles stored")
    return saved


def search_similar_articles(text: str, top_k: int = 5) -> List[Dict]:
    if not text:
        return []
    try:
        vector = _get_article_embeddings([text[:1200]])[0]
    except Exception as exc:
        logger.warning(f"Embedding generation failed for semantic search: {exc}")
        return []

    try:
        client = get_qdrant_client()
        if client is None or not ensure_qdrant_collection():
            return []
        response = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
        )
    except Exception as exc:
        logger.warning(f"Qdrant semantic search failed: {exc}")
        return []

    results = []
    for match in response:
        payload = match.payload or {}
        results.append(
            {
                "title": payload.get("title"),
                "source": payload.get("source"),
                "source_domain": payload.get("source_domain"),
                "published_at": payload.get("published_at"),
                "article_url": payload.get("article_url"),
                "trusted_source": payload.get("trusted_source", False),
                "category": payload.get("category"),
                "summary": payload.get("summary"),
                "score": float(match.score) if match.score is not None else None,
            }
        )
    return results


def fetch_newsapi_articles(query: str, max_articles: int = 20) -> List[Dict]:
    global NEWSAPI_RATE_LIMITED

    if NEWSAPI_RATE_LIMITED:
        return []

    if not Config.NEWS_API_KEY:
        return []

    params = {
        "apiKey": Config.NEWS_API_KEY,
        "q": query,
        "searchIn": "title,description",
        "pageSize": max_articles,
        "language": "en",
        "sortBy": "relevancy",
    }

    resp = requests.get(
        NEWSAPI_ENDPOINT,
        params=params,
        timeout=Config.RSS_FETCH_TIMEOUT,
    )

    if resp.status_code != 200:

        if "rateLimited" in resp.text:
            NEWSAPI_RATE_LIMITED = True
            logger.warning("NewsAPI rate limit reached. Skipping NewsAPI for the remaining queries.")

        else:
            logger.warning(f"NewsAPI fetch failed: {resp.text}")

        return []

    payload = resp.json()
    return payload.get("articles", [])


def fetch_gnews_articles(query: str, max_articles: int = 20) -> List[Dict]:
    if not Config.GNEWS_API_KEY:
        return []
    params = {
        "q": query,
        "token": Config.GNEWS_API_KEY,
        "max": max_articles,
        "lang": "en",
        "in": "title,description,content",
    }
    resp = requests.get(GNEWS_ENDPOINT, params=params, timeout=Config.RSS_FETCH_TIMEOUT)
    if resp.status_code != 200:
        logger.warning(f"GNews fetch failed: {resp.text}")
        return []
    return resp.json().get("articles", [])


def fetch_newsdata_articles(query: str, max_articles: int = 20) -> List[Dict]:
    if not Config.NEWSDATA_API_KEY:
        return []
    params = {
        "apikey": Config.NEWSDATA_API_KEY,
        "q": query,
        "language": "en",
        "page": 1,
    }
    resp = requests.get(NEWSDATA_ENDPOINT, params=params, timeout=Config.RSS_FETCH_TIMEOUT)
    if resp.status_code != 200:
        logger.warning(f"NewsData fetch failed: {resp.text}")
        return []
    return resp.json().get("results", [])


def fetch_mediastack_articles(query: str, max_articles: int = 20) -> List[Dict]:
    api_key = os.getenv("MEDIASTACK_API_KEY")
    if not api_key:
        return []
    params = {
        "access_key": api_key,
        "keywords": query,
        "languages": "en",
        "limit": max_articles,
    }
    resp = requests.get(MEDIASTACK_ENDPOINT, params=params, timeout=Config.RSS_FETCH_TIMEOUT)
    if resp.status_code != 200:
        logger.warning(f"MediaStack fetch failed: {resp.text}")
        return []
    return resp.json().get("data", [])


def safe_requests_get(url: str, timeout: Optional[int] = None, headers: Optional[dict] = None):
    if timeout is None:
        timeout = Config.RSS_FETCH_TIMEOUT
    try:
        response = requests.get(
            url,
            headers={**RSS_REQUEST_HEADERS, **(headers or {})},
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        if url not in _RSS_FEED_ERRORS_LOGGED:
            logger.warning(f"RSS request failed for {url}: {exc}")
            _RSS_FEED_ERRORS_LOGGED.add(url)
        return None


def fetch_rss_feed(url: str, max_items: int = 15) -> List[Dict]:
    try:
        import feedparser

        response = safe_requests_get(url)
        if response is None:
            return []

        feed = feedparser.parse(response.content)
        if feed.bozo:
            bozo_exception = getattr(feed, "bozo_exception", None)
            if url not in _RSS_FEED_ERRORS_LOGGED:
                logger.warning(f"RSS feed parse issue for {url}: {bozo_exception}")
                _RSS_FEED_ERRORS_LOGGED.add(url)

        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "description": entry.get("summary", "") or entry.get("description", ""),
                "content": getattr(entry, "content", [{}])[0].get("value", "") if getattr(entry, "content", None) else "",
                "url": entry.get("link", ""),
                "image_url": entry.get("media_thumbnail", [{}])[0].get("url", "") if entry.get("media_thumbnail") else "",
                "publishedAt": entry.get("published", "") or entry.get("updated", ""),
                "source": entry.get("source", {}).get("title", "") or url,
                "source_domain": entry.get("link", ""),
            })
        return items
    except Exception as exc:
        if url not in _RSS_FEED_ERRORS_LOGGED:
            logger.warning(f"RSS feed failed for {url}: {exc}")
            _RSS_FEED_ERRORS_LOGGED.add(url)
        return []


def get_all_trusted_feeds() -> List[str]:
    return [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "https://indianexpress.com/section/india/feed/",
        "https://www.news18.com/rss/india.xml",
        "https://www.timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://news.google.com/rss",
        "http://rss.cnn.com/rss/edition.rss",
    ]


def start_news_ingestion_scheduler(app):
    if not Config.SCHEDULER_ENABLED:
        logger.info("News ingestion scheduler is disabled")
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    interval_seconds = max(60, Config.INGEST_INTERVAL_MINUTES * 60)

    def _scheduler_loop():
        while True:
            with app.app_context():
                try:
                    ingest_trusted_news()
                except Exception as exc:
                    logger.warning(f"Scheduled news ingestion failed: {exc}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_scheduler_loop, daemon=True, name="news_ingest_scheduler")
    thread.start()