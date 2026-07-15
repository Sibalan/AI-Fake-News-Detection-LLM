from typing import List, Dict

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

MODEL_NAME = "all-MiniLM-L6-v2"

print(f"Loading embedding model: {MODEL_NAME}")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded successfully.")


TRUSTED_SOURCES = {
    "bbc",
    "reuters",
    "associated press",
    "ap",
    "the hindu",
    "indian express",
    "hindustan times",
    "ndtv",
    "times of india",
    "ani",
    "news18",
    "al jazeera",
    "cnn",
    "the guardian",
    "npr",
    "pib",
}


def source_score(source: str) -> float:

    if not source:
        return 0.0

    source = source.lower()

    for trusted in TRUSTED_SOURCES:
        if trusted in source:
            return 1.0

    return 0.0


def rank_articles(
    claim: str,
    articles: List[Dict],
    top_k: int = 5,
) -> List[Dict]:

    if not articles:
        return []

    claim_embedding = model.encode(
        claim,
        convert_to_tensor=True,
    )

    article_texts = [
        " ".join([
            article.get("title", ""),
            article.get("summary", ""),
            article.get("content", ""),
        ])
        for article in articles
    ]

    article_embeddings = model.encode(
        article_texts,
        convert_to_tensor=True,
    )

    similarities = cos_sim(
        claim_embedding,
        article_embeddings,
    )[0]

    scored_articles = []

    for article, similarity in zip(articles, similarities):

        semantic = float(similarity)

        entity = article.get("entity_match_score", 0)

        trusted = source_score(
            article.get("source", "")
        )

        # Normalize entity score
        entity = min(entity / 5.0, 1.0)

        final_score = (
            semantic * 0.60
            + entity * 0.25
            + trusted * 0.15
        )

        article["semantic_score"] = semantic
        article["entity_score"] = entity
        article["trusted_score"] = trusted
        article["final_score"] = final_score

        scored_articles.append(article)

    # Remove duplicate URLs
    unique = {}
    for article in scored_articles:
        url = article.get("url") or article.get("article_url") or ""
        if url and url not in unique:
            unique[url] = article

    scored_articles = list(unique.values())

    scored_articles.sort(
        key=lambda x: x["final_score"],
        reverse=True,
    )

    return scored_articles[:top_k]