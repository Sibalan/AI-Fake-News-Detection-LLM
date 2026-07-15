from flask import Blueprint, request, jsonify, session as flask_session
from flask_jwt_extended import decode_token
from backend.models.news import NewsHistory
from backend.models.prediction import PredictionLog
from backend.models import db
from backend.ml.preprocess import preprocess_text, extract_keywords
from backend.utils.helpers import analyze_sentiment, find_suspicious_phrases
from backend.utils.url_extractor import extract_article_from_url, check_domain_credibility
from backend.ollama_client import analyze_with_phi3
from backend.news_ingest import search_similar_articles
import time
import re
import logging
import traceback

logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")


LOGO_SOURCE_NAMES = [
    "the hindu", "indian express", "times of india", "hindustan times",
    "reuters", "associated press", "ap news", "bbc news", "ndtv", "india today",
    "economic times", "livemint", "mint", "pib", "press information bureau",
    "press trust of india", "pti", "the wire", "the quint", "the print",
    "alt news", "boom live", "fact checker", "fact check", "verified source",
    "trusted source", "verified by", "fact checked by", "source:", "credit:",
    "photo:", "image:", "getty", "istock", "shutterstock", "newspaper",
    "daily mail", "the guardian", "washington post", "new york times", "fox news",
    "cnn", "msnbc", "al jazeera", "the times", "the sun", "daily mirror",
    "the telegraph", "the independent", "the spectator", "economist",
    "news18", "republic world", "times now", "mirror now", "opindia", "swarajya",
]


def clean_ocr_text(text: str) -> str:
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(source in lower for source in LOGO_SOURCE_NAMES) and len(stripped) < 60:
            continue
        cleaned_lines.append(stripped)
    text = " ".join(cleaned_lines)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(.)\1{4,}", r"\1\1\1", text)
    text = re.sub(r"\b(\w)\s(?=\w\s)", r"\1", text)
    text = re.sub(
        r"\b(\w)\s(\w)\b",
        lambda m: (
            m.group(1) + m.group(2)
            if len(m.group(1)) == 1 and len(m.group(2)) == 1
            else m.group(0)
        ),
        text,
    )
    text = re.sub(r"[^\w\s\.\,\!\?\-\'\:\;\(\)\[\]\{\}\"\/\@\#\$\%\&\*]", "", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\s+,", ",", text)
    text = " ".join(text.split())
    return text.strip()


def get_current_user_id():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        try:
            decoded = decode_token(token)
            return int(decoded["sub"])
        except Exception:
            pass
    return flask_session.get("user_id")


def _run_analysis(news_text: str, source_url: str, source_type: str):
    """Core analysis pipeline — shared between text and URL routes."""
    start_time = time.time()

    cleaned = clean_ocr_text(news_text)
    if cleaned != news_text:
        logger.info(f"OCR text cleaned: {len(news_text)} -> {len(cleaned)} chars")
        news_text = cleaned

    preprocessed = preprocess_text(news_text)
    keywords = extract_keywords(news_text)
    sentiment, sentiment_score = analyze_sentiment(news_text)
    suspicious = find_suspicious_phrases(news_text)

    try:
        req = request.get_json(silent=True) or {}
        display_policy = (req.get('display_policy') or '').strip() or None
    except Exception:
        display_policy = None

    phi3_result = analyze_with_phi3(news_text, display_policy=display_policy, source_type=source_type)
    print("\n========== PHI3 RESULT ==========")
    print(phi3_result)
    print("=================================\n")

    raw_prediction = phi3_result["prediction"]
    confidence = phi3_result["confidence"]
    display_prediction = phi3_result.get("display_prediction", raw_prediction)
    is_misleading_flag = phi3_result.get("is_misleading", False)
    explanation = phi3_result["explanation"]
    fact_checks = phi3_result.get("fact_checks", [])
    llm_source = phi3_result.get("llm_source", "")
    category = phi3_result.get("category", "General")
    method_label = phi3_result.get("method") or (llm_source if llm_source else "AI")

    xai_reasons = phi3_result.get("xai_reasons", [])
    xai_suspicious = phi3_result.get("xai_suspicious_phrases", suspicious)
    manipulation_type = phi3_result.get("manipulation_type", "None")
    news_api_articles = phi3_result.get("news_api_articles", [])

    try:
        related_articles = search_similar_articles(news_text)
    except Exception as e:
        logger.warning(f"Related article search failed: {e}")
        related_articles = []

    processing_time = round(time.time() - start_time, 2)

    flask_session["assistant_context"] = {
        "article_text": news_text,
        "prediction": display_prediction,
        "confidence": confidence,
        "explanation": explanation,
        "source_type": source_type,
    }

    user_id = get_current_user_id()
    try:
        history = NewsHistory(
            user_id=user_id,
            news_text=news_text,
            prediction=display_prediction,
            confidence=confidence,
            explanation=explanation,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            keywords=",".join(keywords),
            suspicious_phrases=",".join(xai_suspicious or suspicious),
            source_url=source_url or None,
            source_type=source_type,
            processing_time=processing_time,
            method="phi3",
        )
        db.session.add(history)

        log = PredictionLog(
            user_id=user_id,
            news_text=news_text[:500],
            prediction=display_prediction,
            confidence=confidence,
            method="phi3",
            processing_time=processing_time,
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as db_err:
        logger.warning(f"DB save failed (prediction still works): {db_err}")
        db.session.rollback()

    return {
        "prediction": display_prediction,
        "display_prediction": display_prediction,
        "raw_prediction": raw_prediction,
        "is_misleading": is_misleading_flag,
        "confidence": confidence,
        "explanation": explanation,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "keywords": keywords,
        "suspicious_phrases": xai_suspicious or suspicious,
        "word_count": preprocessed["word_count"],
        "processing_time": processing_time,
        "method": method_label,
        "llm_source": llm_source,
        "fact_checks": fact_checks,
        "category": category,
        "model_verdict": phi3_result.get("model_verdict"),
        "trusted_source_count": phi3_result.get("trusted_source_count", 0),
        "xai_reasons": xai_reasons,
        "manipulation_type": manipulation_type,
        "news_api_articles": news_api_articles,
        "related_articles": related_articles,
    }


@predict_bp.route("/", methods=["POST"])
def predict_news():
    try:
        data = request.get_json()
        news_text = (data.get("text") or "").strip()
        source_url = (data.get("source_url") or "").strip()
        source_type = (data.get("source_type") or "text").strip().lower() or "text"

        if not news_text:
            return jsonify({"error": "News text is required"}), 400
        if len(news_text) < 5:
            return jsonify({"error": "Please enter at least 5 characters for analysis"}), 400

        result = _run_analysis(news_text, source_url, source_type)

        if source_url:
            result["source_credibility"] = check_domain_credibility(source_url)

        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        logger.exception("Prediction error")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@predict_bp.route("/url", methods=["POST"])
def analyze_url():
    """Extract article from URL and analyze it."""
    try:
        data = request.get_json()
        url = (data.get("url") or "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400
        if not url.startswith(("http://", "https://")):
            return jsonify({"error": "URL must start with http:// or https://"}), 400

        extracted = extract_article_from_url(url)

        if extracted.get("error") and not extracted.get("text"):
            return jsonify({"error": extracted["error"]}), 422

        title = extracted.get("title", "")
        body = extracted.get("text", "")
        news_text = (f"{title}. {body}" if title else body).strip()

        if len(news_text) < 20:
            return jsonify({"error": "Could not extract enough readable content from this URL."}), 422

        result = _run_analysis(news_text[:3000], url, "url")
        result["extracted_title"] = title
        result["extracted_text_preview"] = body[:500]
        result["source_credibility"] = extracted.get("credibility")
        result["source_domain"] = extracted.get("source", "")

        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        logger.exception("Prediction error")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@predict_bp.route("/credibility", methods=["POST"])
def check_credibility():
    """Quick domain credibility check without full analysis."""
    data = request.get_json()
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "URL required"}), 400
    return jsonify(check_domain_credibility(url)), 200