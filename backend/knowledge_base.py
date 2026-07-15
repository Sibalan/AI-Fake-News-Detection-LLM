import json
import os
from typing import Optional

BASE_DIR = os.path.dirname(__file__)

KNOWLEDGE_FILE = os.path.join(
    BASE_DIR,
    "knowledge_base.json"
)


def load_knowledge_base():
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def verify_from_knowledge_base(news_text: str):
    kb = load_knowledge_base()

    text = news_text.lower().strip()

    for category in kb.values():
        if not isinstance(category, dict):
            continue

        for subject, answer in category.items():
            if (
                subject in text
                or all(word in text for word in subject.split())
            ):
                if answer.lower() in text:
                    return {
                        "found": True,
                        "prediction": "REAL",
                        "confidence": 99,
                        "explanation": f"The statement matches the verified knowledge base. {subject.title()} is {answer}."
                    }
                else:
                    return {
                        "found": True,
                        "prediction": "FAKE",
                        "confidence": 99,
                        "explanation": f"The statement contradicts the verified knowledge base. {subject.title()} is {answer}, not the value given in the text."
                    }

    return {
        "found": False
    }