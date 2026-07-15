from typing import Dict, List


def filter_articles(
    articles: List[Dict],
    entities: Dict,
) -> List[Dict]:

    if not articles:
        return []

    search_terms = []

    for key, value in entities.items():
        if isinstance(value, list):
            for item in value:
                if item and isinstance(item, str):
                    search_terms.append(item.lower())

    filtered_articles = []

    for article in articles:

        text = " ".join([
            article.get("title", ""),
            article.get("summary", ""),
            article.get("description", ""),
            article.get("content", ""),
        ]).lower()

        score = 0

        for term in search_terms:
            if term in text:
                score += 1

        # Add the article only ONCE after checking all terms
        if score >= 1:
            article["entity_match_score"] = score
            filtered_articles.append(article)

    filtered_articles.sort(
        key=lambda x: x.get("entity_match_score", 0),
        reverse=True,
    )

    return filtered_articles