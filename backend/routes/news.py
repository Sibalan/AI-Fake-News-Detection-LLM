import logging
from flask import Blueprint, request, jsonify

from utils.news_api import fetch_latest_news, fetch_breaking_news, NewsApiError
from groq_client import groq_available, summarize_text_with_groq

logger = logging.getLogger(__name__)
news_bp = Blueprint("news", __name__)


def _build_summary(article: dict) -> str:
    source_text = article.get("description") or article.get("title") or ""
    if not source_text or len(source_text) < 40:
        return ""
    if len(source_text) > 900:
        source_text = source_text[:900].rsplit(" ", 1)[0]
    return summarize_text_with_groq(source_text) or ""


def _enrich(articles: list, add_summary: bool = True) -> list:
    result = []
    for article in articles:
        summary = _build_summary(article) if add_summary and groq_available() else ""
        result.append({
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "image_url": article.get("image_url", ""),
            "source": article.get("source", ""),
            "published": article.get("published", ""),
            "summary": summary,
        })
    return result


@news_bp.route("/get_news", methods=["GET"])
def get_news():
    category = request.args.get("category", "world").strip()
    no_summary = request.args.get("no_summary", "false").lower() == "true"

    try:
        articles = fetch_latest_news(category)
    except NewsApiError as exc:
        logger.warning(f"News fetch failed for '{category}': {exc}")
        return jsonify({"error": str(exc)}), 500

    enriched = _enrich(articles, add_summary=not no_summary)
    return jsonify({"articles": enriched, "category": category, "count": len(enriched)}), 200


@news_bp.route("/get_breaking_news", methods=["GET"])
def get_breaking_news():
    try:
        articles = fetch_breaking_news(max_articles=8)
    except NewsApiError as exc:
        logger.warning(f"Breaking news fetch failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    # No summaries for breaking news ticker — keep it fast
    enriched = _enrich(articles, add_summary=False)
    return jsonify({"articles": enriched}), 200
