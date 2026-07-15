import json
import logging
import os
import requests

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def verify_evidence(claim: str, evidence: str):
    """
    Verify whether one evidence article supports,
    contradicts, or is irrelevant to a claim.
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not found.")
        return None

    prompt = f"""
You are an expert fact-checking AI.

You are given ONE claim and ONE evidence article.

Your task is NOT to determine whether the claim is globally true.

Your ONLY task is to decide whether THIS evidence:

1. SUPPORTS the claim
2. CONTRADICTS the claim
3. is IRRELEVANT to the claim

Claim:
{claim}

Evidence:
{evidence}

IMPORTANT RULES:

- SUPPORT = The evidence directly confirms the claim.
- CONTRADICT = The evidence directly disproves the claim.
- IRRELEVANT = The evidence talks about the same topic or people but does not prove or disprove the claim.

Respond ONLY with valid JSON.

Example:

{{
    "verdict":"SUPPORT",
    "confidence":96,
    "reason":"The evidence explicitly confirms the claim."
}}
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0,
        "max_tokens": 150,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )

        if response.status_code != 200:
            logger.error(f"Groq API Error: {response.status_code}")
            return None

        content = response.json()["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Groq did not return valid JSON.")
            return {
                "verdict": "IRRELEVANT",
                "confidence": 0,
                "reason": content,
            }

    except Exception as e:
        logger.exception(f"Groq verification failed: {e}")
        return None