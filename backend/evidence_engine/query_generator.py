from typing import List
from evidence_engine.entity_extractor import extract_entities


def generate_queries(claim: str) -> List[str]:
    """
    Generate multiple search queries from a claim.
    """

    info = extract_entities(claim)

    subject = info["subject"].strip()
    relation = info["relation"].strip()
    obj = info["object"].strip()

    queries = []

    # Original claim
    queries.append(claim)

    # Subject only
    if subject:
        queries.append(subject)

    # Object only
    if obj:
        queries.append(obj)

    # Subject + Object
    if subject and obj:
        queries.append(f"{subject} {obj}")

    # Relation query
    if relation and subject:
        queries.append(f"{subject} {relation}")

    # Reverse query
    if subject and obj:
        queries.append(f"{obj} {subject}")

    # Remove duplicates
    queries = list(dict.fromkeys(q.strip() for q in queries if q.strip()))

    return queries