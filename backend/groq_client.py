import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def analyze_with_groq(news_text: str, recent_context: str = "") -> Optional[str]:
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set - skipping Groq inference")
        return None

    if len(news_text.strip()) < 5:
        return None

    context_block = ""
    if recent_context:
        context_block = (
            f"\n\nLIVE NEWS CONTEXT (real articles fetched right now from News API):\n"
            f"{recent_context}\n"
            f"Use these articles to confirm OR contradict the claim. They reflect current reality.\n"
        )
    else:
        context_block = "\n\nLIVE NEWS CONTEXT: No matching articles found in News API.\n"

    try:
        prompt = f"""You are an expert AI fact-checker and misinformation analyst. Analyze the exact news text provided and determine if it is REAL or FAKE.

YOUR KNOWLEDGE CUTOFF: Early 2025. For 2025-2026 events, rely on the Live News Context below.
{context_block}
HOW TO USE LIVE CONTEXT:
- Context CONFIRMS the exact claim → strong evidence for REAL
- Context CONTRADICTS/SUPERSEDES the claim → strong evidence for FAKE
- For current roles/positions (CM, PM, CEO, sports results), context is MORE reliable than your training data

NEWS TEXT TO ANALYZE:
"{news_text[:2000]}"

CRITICAL INSTRUCTIONS:
1. Read the EXACT text above carefully word by word.
2. Your reasons must reference SPECIFIC WORDS, PHRASES, or CLAIMS from the text — not generic observations.
3. If the text mentions a specific person, place, date, event, or fact — address it directly.
4. Quote exact phrases from the text in your reasons.

Respond EXACTLY in this format (no markdown, no extra text):

VERDICT: [REAL or FAKE]
CONFIDENCE: [75-99]
REASON_1: [Specific reason citing exact words/phrases from the text]
REASON_2: [Specific reason about the claims or facts in the text]
REASON_3: [Specific reason about language patterns or source signals in the text]
SUSPICIOUS_PHRASES: [exact phrases from the text that are suspicious, comma-separated, or NONE]
MANIPULATION_TYPE: [ONE of: Clickbait | Conspiracy | Pseudoscience | Death Hoax | Outdated Info | Misattribution | Satire | Emotional Manipulation | None]
EXPLANATION: [1-2 sentence final verdict summary referencing what specifically was found in the text]"""

        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 500,
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


def summarize_text_with_groq(text: str) -> Optional[str]:
    if not GROQ_API_KEY or not text.strip():
        return None

    try:
        prompt = f"""Summarize the following news content in 1-2 concise sentences that capture the key facts:

"{text[:1500]}"

Respond with only the summary, no extra text."""

        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 150,
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return content.strip() or None
    except Exception as e:
        logger.error(f"Groq summarize error: {e}")
        return None


def parse_groq_structured(raw: str) -> dict:
    """Parse the structured Groq response into a dict with reasons, manipulation type, etc."""
    result = {
        "verdict": None,
        "confidence": None,
        "reasons": [],
        "suspicious_phrases": [],
        "manipulation_type": "None",
        "explanation": "",
    }
    if not raw:
        return result

    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("VERDICT:"):
            v = line.split(":", 1)[1].strip().upper()
            result["verdict"] = "REAL" if "REAL" in v else ("FAKE" if "FAKE" in v else None)
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("REASON_"):
            r = line.split(":", 1)[1].strip()
            if r:
                result["reasons"].append(r)
        elif line.startswith("SUSPICIOUS_PHRASES:"):
            sp = line.split(":", 1)[1].strip()
            if sp.upper() != "NONE" and sp:
                result["suspicious_phrases"] = [p.strip() for p in sp.split(",") if p.strip()]
        elif line.startswith("MANIPULATION_TYPE:"):
            result["manipulation_type"] = line.split(":", 1)[1].strip()
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.split(":", 1)[1].strip()

    return result
