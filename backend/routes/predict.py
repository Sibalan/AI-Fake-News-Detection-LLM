from flask import Blueprint, request, jsonify, session as flask_session
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from models.news import NewsHistory
from models.prediction import PredictionLog
from models import db
from ml.preprocess import preprocess_text, extract_keywords
from utils.helpers import analyze_sentiment, find_suspicious_phrases
from ollama_client import analyze_with_phi3
import time
import re
import logging

logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")


LOGO_SOURCE_NAMES = [
    "the hindu",
    "indian express",
    "times of india",
    "hindustan times",
    "reuters",
    "associated press",
    "ap news",
    "bbc news",
    "ndtv",
    "india today",
    "economic times",
    "livemint",
    "mint",
    "pib",
    "press information bureau",
    "press trust of india",
    "pti",
    "the wire",
    "the quint",
    "the print",
    "alt news",
    "boom live",
    "fact checker",
    "fact check",
    "verified source",
    "trusted source",
    "verified by",
    "fact checked by",
    "source:",
    "credit:",
    "photo:",
    "image:",
    "getty",
    "istock",
    "shutterstock",
    "newspaper",
    "daily mail",
    "the guardian",
    "washington post",
    "new york times",
    "fox news",
    "cnn",
    "msnbc",
    "al jazeera",
    "the times",
    "the sun",
    "daily mirror",
    "the telegraph",
    "the independent",
    "the spectator",
    "economist",
    "news18",
    "republic world",
    "times now",
    "mirror now",
    "opindia",
    "swarajya",
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


@predict_bp.route("/", methods=["POST"])
def predict_news():
    start_time = time.time()
    try:
        data = request.get_json()
        news_text = data.get("text", "").strip()
        source_url = data.get("source_url", "").strip()
        source_type = data.get("source_type", "text").strip().lower() or "text"

        if not news_text:
            return jsonify({"error": "News text is required"}), 400

        if len(news_text) < 5:
            return jsonify(
                {"error": "Please enter at least 5 characters for analysis"}
            ), 400

        cleaned = clean_ocr_text(news_text)
        if cleaned != news_text:
            logger.info(f"OCR text cleaned: {len(news_text)} -> {len(cleaned)} chars")
            news_text = cleaned

        user_id = get_current_user_id()

        preprocessed = preprocess_text(news_text)
        keywords = extract_keywords(news_text)
        sentiment, sentiment_score = analyze_sentiment(news_text)
        suspicious = find_suspicious_phrases(news_text)

        phi3_result = analyze_with_phi3(news_text)

        prediction = phi3_result["prediction"]
        confidence = phi3_result["confidence"]
        explanation = phi3_result["explanation"]
        fact_checks = phi3_result.get("fact_checks", [])
        llm_source = phi3_result.get("llm_source", "")
        category = phi3_result.get("category", "General")

        method_label = phi3_result.get("method") or (llm_source if llm_source else "AI")

        processing_time = round(time.time() - start_time, 2)

        try:
            history = NewsHistory(
                user_id=user_id,
                news_text=news_text,
                prediction=prediction,
                confidence=confidence,
                explanation=explanation,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                keywords=",".join(keywords),
                suspicious_phrases=",".join(suspicious),
                source_url=source_url or None,
                source_type=source_type,
                processing_time=processing_time,
                method="phi3",
            )
            db.session.add(history)

            log = PredictionLog(
                user_id=user_id,
                news_text=news_text[:500],
                prediction=prediction,
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

        result = {
            "prediction": prediction,
            "confidence": confidence,
            "explanation": explanation,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "keywords": keywords,
            "suspicious_phrases": suspicious,
            "word_count": preprocessed["word_count"],
            "processing_time": processing_time,
            "method": method_label,
            "llm_source": llm_source,
            "fact_checks": fact_checks,
            "category": category,
            "model_verdict": phi3_result.get("model_verdict"),
            "trusted_source_count": phi3_result.get("trusted_source_count", 0),
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
