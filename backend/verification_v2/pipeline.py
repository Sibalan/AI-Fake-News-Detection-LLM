from verification_v2.article_filter import filter_articles
from verification_v2.entity_extractor import extract_entities
from verification_v2.query_generator import generate_queries
from verification_v2.evidence_fetcher import fetch_evidence
from verification_v2.evidence_ranker import rank_articles
from verification_v2.groq_verifier import verify_evidence
from verification_v2.verdict_aggregator import aggregate_verdicts


def verify_claim(claim: str) -> dict:

    print("=" * 60)
    print("Verification V2")
    print("=" * 60)

    print("Claim:", claim)

    print("\nExtracting entities...")
    entities = extract_entities(claim)
    print("Entities extracted.")

    print("\nGenerating search queries...")
    queries = generate_queries(entities)
    print(f"Generated {len(queries)} search queries.")

    print("\nFetching evidence...")
    articles = fetch_evidence(queries)
    print(f"Retrieved {len(articles)} articles.")

    print("\nFiltering relevant articles...")
    articles = filter_articles(
        articles,
        entities,
    )
    print(f"Remaining after filtering: {len(articles)} articles.")

    # Step 2: Rank evidence
    print("\nRanking evidence...")
    top_articles = rank_articles(
        claim,
        articles,
        top_k=5,
    )
    print(f"Selected {len(top_articles)} best articles.")

    # Step 3: Verify each article with Groq
    print("\nVerifying evidence with Groq...")
    verification_results = []

    for article in top_articles:
        evidence_text = " ".join([
            article.get("title", ""),
            article.get("summary", ""),
            article.get("content", "")
        ])

        result = verify_evidence(
            claim,
            evidence_text,
        )

        if result:
            result["source"] = article.get("source", "Unknown")
            result["url"] = article.get("url", "")
            verification_results.append(result)

    # Step 4: Aggregate all verification results
    print("\nAggregating final verdict...")
    final_result = aggregate_verdicts(
        verification_results
    )

    print("\nVerification Complete.")
    print("=" * 60)

    return {
        "claim": claim,
        "prediction": final_result["prediction"],
        "confidence": final_result["confidence"],
        "support_count": final_result["support_count"],
        "contradict_count": final_result["contradict_count"],
        "irrelevant_count": final_result["irrelevant_count"],
        "verified_articles": verification_results,
    }