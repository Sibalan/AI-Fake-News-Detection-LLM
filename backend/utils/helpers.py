import re
import time
import logging
from textblob import TextBlob

logger = logging.getLogger(__name__)


def analyze_sentiment(text):
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.2:
            return "Positive", polarity
        elif polarity < -0.2:
            return "Negative", polarity
        else:
            return "Neutral", polarity
    except Exception as e:
        logger.warning(f"Sentiment analysis failed: {e}")
        return "Neutral", 0.0


def find_suspicious_phrases(text):
    suspicious_patterns = [
        (r"\bshock\b", "Sensationalism"),
        (r"\byou won\'?t believe\b", "Clickbait"),
        (r"\b(viral|trending)\b", "Viral claim"),
        (r"\b(conspiracy|cover.?up)\b", "Conspiracy language"),
        (r"\b(they don\'?t want you to know)\b", "Secrecy claim"),
        (r"\b(100%|guaranteed|proven)\b", "Exaggeration"),
        (r"\b(doctors hate|doctors don\'?t want)\b", "Misleading medical"),
        (r"\b(big pharma|government hiding)\b", "Distrust language"),
        (r"\b(breaking|exclusive|urgent)\b", "Urgency language"),
        (r"\b(they are lying|mainstream media won\'?t)\b", "Media distrust"),
    ]
    found = []
    for pattern, label in suspicious_patterns:
        if re.search(pattern, text.lower()):
            found.append(label)
    return found


def calculate_confidence_from_score(score):
    return min(max(abs(score) * 100, 50), 99)


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        if isinstance(result, tuple):
            return (*result, elapsed)
        return result, elapsed

    return wrapper
