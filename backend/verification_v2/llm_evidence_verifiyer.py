import json
import groq_client


SYSTEM_PROMPT = """
You are an expert fact-checking assistant.

You are given:

1. A user claim.
2. ONE evidence article.

Your job is ONLY to determine whether THIS article:

- SUPPORTS the claim
- CONTRADICTS the claim
- is IRRELEVANT

Do NOT verify from your own knowledge.

Judge ONLY from the supplied evidence.

Return ONLY valid JSON.

Example:

{
  "verdict":"SUPPORT",
  "confidence":96,
  "reason":"The article explicitly confirms the claim."
}
"""


def verify_article(claim: str, article: dict):

    prompt = f"""
Claim:

{claim}

Evidence Title:

{article.get("title","")}

Evidence Summary:

{article.get("summary","")}

Source:

{article.get("source","")}
"""

    try:

        response = groq_client.ask_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0,
        )

        data = json.loads(response)

        return data

    except Exception:

        return {
            "verdict": "IRRELEVANT",
            "confidence": 0,
            "reason": "Unable to verify evidence."
        }