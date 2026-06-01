import logging
from flask import Blueprint, request, jsonify

from utils.news_api import fetch_latest_news, NewsApiError
from groq_client import groq_available, summarize_text_with_groq

logger = logging.getLogger(__name__)
news_bp = Blueprint("news", __name__)


def _build_summary(article: dict) -> str:
    source_text = article.get("description") or article.get("title") or ""
    if not source_text:
        return ""

    if len(source_text) > 900:
        source_text = source_text[:900].rsplit(" ", 1)[0]

    return summarize_text_with_groq(source_text) or ""


@news_bp.route("/get_news", methods=["GET"])
def get_news():
    category = request.args.get("category", "international").strip()
    try:
        articles = fetch_latest_news(category)
    except NewsApiError as exc:
        logger.warning(f"News fetch failed: {exc}")
        return jsonify({"error": "Unable to fetch news"}), 500

    if not articles:
        return jsonify({"error": "Unable to fetch news"}), 500

    if groq_available():
        optimized_articles = []
        for article in articles:
            summary = _build_summary(article)
            optimized_articles.append({
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
                "summary": summary,
            })
        articles = optimized_articles
    else:
        articles = [
            {"title": a["title"], "description": a["description"], "url": a["url"], "summary": ""}
            for a in articles
        ]

    return jsonify({"articles": articles}), 200
