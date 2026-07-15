from typing import Dict, List


def generate_queries(entities: Dict) -> List[str]:

    queries = []

    queries.extend(entities.get("search_queries", []))

    people = entities.get("people", [])
    organizations = entities.get("organizations", [])
    locations = entities.get("locations", [])
    roles = entities.get("roles", [])
    events = entities.get("events", [])
    keywords = entities.get("keywords", [])

    all_entities = []

    all_entities.extend(people)
    all_entities.extend(organizations)
    all_entities.extend(locations)
    all_entities.extend(roles)
    all_entities.extend(events)
    all_entities.extend(keywords)

    all_entities = list(dict.fromkeys(
        e.strip()
        for e in all_entities
        if e and e.strip()
    ))

    # Quoted entities
    for entity in all_entities:
        queries.append(f'"{entity}"')

    # Pairwise combinations
    for i in range(len(all_entities)):
        for j in range(i + 1, len(all_entities)):
            queries.append(f'"{all_entities[i]}" "{all_entities[j]}"')

    # Unquoted combinations
    for i in range(len(all_entities)):
        for j in range(i + 1, len(all_entities)):
            queries.append(f"{all_entities[i]} {all_entities[j]}")

    queries = list(dict.fromkeys(
        q.strip()
        for q in queries
        if q and q.strip()
    ))

    return queries[:10]