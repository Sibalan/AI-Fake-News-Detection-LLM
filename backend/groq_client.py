import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def analyze_with_groq(news_text: str) -> Optional[str]:
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set - skipping Groq inference")
        return None

    if len(news_text.strip()) < 5:
        return None

    try:
        prompt = f"""You are a strict AI fact-checker. Determine if the following news text is REAL (factually correct) or FAKE (false/misinformation).

Rules:
- FAKE indicators: factual contradictions, role mismatches, conspiracy claims, clickbait, emotional manipulation, unverifiable claims, vague sources
- REAL indicators: specific verifiable facts, named official sources, measured language, peer-reviewed references, consistency with known facts
- Evaluate the CLAIM itself — do NOT trust or distrust based on which source name appears in the text (logos, mastheads, badges can be misleading)
- If the text is a short factual statement with no clear misinformation signals, evaluate it based on plausibility
- Default to FAKE only when there are clear misinformation signals or the claim contradicts well-known facts
- If the claim appears plausible and has no obvious misinformation markers, mark it REAL

News text: "{news_text[:2000]}"

Respond EXACTLY in this format (no extra text):
VERDICT: [REAL or FAKE]
CONFIDENCE: [85-99]
EXPLANATION: [1-2 sentences explaining your reasoning]"""

        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 400,
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )

        if resp.status_code != 200:
            logger.warning(f"Groq API returned {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if content and content.strip():
            logger.info(f"Groq API response received ({len(content)} chars)")
            return content.strip()

        logger.warning("Groq returned empty response")
        return None

    except requests.exceptions.Timeout:
        logger.warning("Groq API timed out (15s)")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("Groq API connection error")
        return None
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None


def groq_available() -> bool:
    return bool(GROQ_API_KEY)
