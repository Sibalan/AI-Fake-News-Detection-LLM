from typing import Optional, Dict

STATIC_KNOWLEDGE = {

    "capital of india": "New Delhi",
    "capital of west bengal": "Kolkata",
    "capital of tamil nadu": "Chennai",
    "capital of karnataka": "Bengaluru",
    "capital of kerala": "Thiruvananthapuram",

    "currency of india": "Indian Rupee",

    "headquarters of who": "Geneva",

    "headquarters of isro": "Bengaluru",

}

def resolve_knowledge(claim: str) -> Optional[Dict]:
    """
    Check whether a claim matches our static knowledge base.
    """

    claim_lower = claim.lower().strip()

    for key, value in STATIC_KNOWLEDGE.items():

        if key in claim_lower:

            return {
                "found": True,
                "query": key,
                "correct_answer": value,
                "source": "Knowledge Base"
            }

    return None