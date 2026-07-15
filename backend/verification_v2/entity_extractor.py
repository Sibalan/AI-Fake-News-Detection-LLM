import json
import logging
import os
from typing import Dict

import requests
import re
from dotenv import load_dotenv

load_dotenv()
print("Current Working Directory:", os.getcwd())
print("GROQ_API_KEY Loaded:", bool(os.getenv("GROQ_API_KEY")))

logger = logging.getLogger(__name__)

# ----------------------------
# ADD THIS FUNCTION HERE
# ----------------------------

def fallback_entity_extractor(claim: str) -> Dict:
    """
    Rule-based fallback entity extractor.
    Used when Groq is unavailable or rate-limited.
    """

    roles = [
        "President",
        "Prime Minister",
        "Chief Minister",
        "Governor",
        "CEO",
        "Founder",
        "Captain",
        "Chairman",
        "Minister",
    ]

    found_roles = [
        role for role in roles
        if role.lower() in claim.lower()
    ]

    years = re.findall(r"\b(19\d{2}|20\d{2}|21\d{2})\b", claim)
    numbers = re.findall(r"\b\d+\b", claim)

    entities = re.findall(
        r"\b[A-Z][a-zA-Z.]+(?:\s+[A-Z][a-zA-Z.]+)*",
        claim,
    )

    keywords = [
        word
        for word in re.findall(r"[A-Za-z]+", claim)
        if len(word) > 3
    ]

    return {
        "category": "general",
        "people": entities,
        "organizations": [],
        "locations": [],
        "roles": found_roles,
        "events": [],
        "products": [],
        "technologies": [],
        "dates": years,
        "numbers": numbers,
        "keywords": keywords,
        "search_queries": [
            claim,
            *entities[:3],
        ],
    }

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODEL = "llama-3.3-70b-versatile"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_entities(claim: str) -> Dict:
    """
    Extract structured entities from a news claim.

    Returns JSON like:

    {
        "category": "...",
        "people": [],
        "organizations": [],
        "locations": [],
        "roles": [],
        "events": [],
        "products": [],
        "technologies": [],
        "dates": [],
        "numbers": [],
        "keywords": [],
        "search_queries": []
    }
    """

    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not found.")
        return {}

    prompt = f"""
You are an expert news information extraction system.

Your job is to understand ANY news claim.

The claim may belong to ANY category including:

- Politics
- Sports
- Technology
- Business
- Finance
- Economy
- Entertainment
- Health
- Science
- Artificial Intelligence
- Crime
- Education
- Environment
- International Relations
- Defense
- Space
- Cybersecurity
- General
- Other

Extract ALL useful information.

Return ONLY valid JSON.

JSON Schema:

{{
    "category": "",
    "people": [],
    "organizations": [],
    "locations": [],
    "roles": [],
    "events": [],
    "products": [],
    "technologies": [],
    "dates": [],
    "numbers": [],
    "keywords": [],
    "search_queries": []
}}

Rules:

1. Detect the primary category.
2. Extract every important entity.
3. Generate 5 high-quality search queries.
4. Search queries should contain the important entities.
5. Return ONLY valid JSON.
6. Do NOT explain anything.

Claim:

{claim}
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
        "max_tokens": 400,
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
            logger.warning(
                f"Groq returned {response.status_code}: {response.text}"
            )
            logger.info("Using fallback entity extractor.")
            return fallback_entity_extractor(claim)

        content = (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        # Remove markdown if Groq returns ```json
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        return json.loads(content)

    except json.JSONDecodeError:
        logger.error("Groq returned invalid JSON.")
        logger.info("Using fallback entity extractor.")
        return fallback_entity_extractor(claim)

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        logger.info("Using fallback entity extractor.")
        return fallback_entity_extractor(claim)