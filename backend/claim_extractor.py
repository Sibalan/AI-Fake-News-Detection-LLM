import re
from typing import Dict

RELATION_PATTERNS = {
    "capital of": "Capital",
    "prime minister of": "Prime Minister",
    "chief minister of": "Chief Minister",
    "president of": "President",
    "governor of": "Governor",
    "chief justice of": "Chief Justice",
    "currency of": "Currency",
    "ceo of": "CEO",
    "founder of": "Founder",
    "headquarters of": "Headquarters",
}


def extract_claim(text: str) -> Dict:
    """
    Extract Subject, Relation and Object from a factual statement.
    """
    claim = {
        "subject": "",
        "relation": "",
        "object": "",
        "original_text": text.strip()
    }

    text = text.strip()

    # ----------------------------------------
    # 1. "won" pattern  e.g. "India won the match"
    # ----------------------------------------
    won_match = re.search(r"(.+?)\s+won\s+(.+)", text, re.IGNORECASE)
    if won_match:
        claim["subject"] = won_match.group(1).strip()
        claim["relation"] = "Winner"
        claim["object"] = won_match.group(2).strip()
        return claim

    # ----------------------------------------
    # 2. "is" pattern  e.g. "Capital of India is New Delhi"
    # ----------------------------------------
    is_match = re.search(r"(.+?)\s+is\s+(.+)", text, re.IGNORECASE)
    if is_match:
        left = is_match.group(1).strip()
        right = is_match.group(2).strip()

        for pattern, relation in RELATION_PATTERNS.items():
            if left.lower().startswith(pattern):
                claim["subject"] = left[len(pattern):].strip()
                claim["relation"] = relation
                claim["object"] = right
                return claim

        # "is" found but no known relation pattern matched
        claim["subject"] = left
        claim["relation"] = "Is"          # ← was left blank before
        claim["object"] = right
        return claim

    # ----------------------------------------
    # 3. Fallback — headlines / OCR / no verb
    # ----------------------------------------
    words = text.split()
    claim["subject"] = " ".join(words[:8]).strip()
    claim["relation"] = "Statement"
    claim["object"] = text
    return claim