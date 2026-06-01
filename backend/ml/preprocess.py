import re
import nltk
import logging

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("punkt_tab", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

logger = logging.getLogger(__name__)

STOPWORDS = set(stopwords.words("english"))


def clean_text(text):
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text):
    return word_tokenize(text)


def remove_stopwords(tokens):
    return [word for word in tokens if word not in STOPWORDS and len(word) > 2]


def preprocess_text(text):
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    tokens = remove_stopwords(tokens)
    return {
        "cleaned_text": cleaned,
        "tokens": tokens,
        "cleaned_preview": " ".join(tokens),
        "word_count": len(tokens),
    }


def extract_keywords(text, top_n=10):
    from collections import Counter

    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    tokens = remove_stopwords(tokens)
    freq = Counter(tokens)
    return [word for word, _ in freq.most_common(top_n)]
