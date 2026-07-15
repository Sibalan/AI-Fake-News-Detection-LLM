def combine_verdicts(results):
    """
    Combine individual evidence verdicts into one final verdict.
    """

    supports = 0
    contradicts = 0
    irrelevant = 0

    support_articles = []
    contradict_articles = []

    for result in results:

        verdict = result["verdict"].upper()

        if verdict == "SUPPORTS":
            supports += 1
            support_articles.append(result["article"]["title"])

        elif verdict == "CONTRADICTS":
            contradicts += 1
            contradict_articles.append(result["article"]["title"])

        else:
            irrelevant += 1

    # ------------------------
    # Decide Final Verdict
    # ------------------------

    if contradicts > supports:

        final_verdict = "FAKE"

        confidence = min(95, 60 + contradicts * 10)

        explanation = (
            f"{contradicts} evidence article(s) contradict the claim."
        )

    elif supports > contradicts:

        final_verdict = "REAL"

        confidence = min(95, 60 + supports * 10)

        explanation = (
            f"{supports} evidence article(s) support the claim."
        )

    else:

        final_verdict = "UNCERTAIN"

        confidence = 50

        explanation = "Evidence is mixed or insufficient."

    return {
        "verdict": final_verdict,
        "confidence": confidence,
        "supports": supports,
        "contradicts": contradicts,
        "irrelevant": irrelevant,
        "support_articles": support_articles,
        "contradict_articles": contradict_articles,
        "explanation": explanation,
    }