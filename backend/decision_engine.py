from evidence_ranker import calculate_evidence_score
from typing import Dict, List


def decide_verdict(
    llm_verdict: str,
    llm_confidence: float,
    pipeline_result: Dict,
    fact_check_results: List,
    supported_trusted: List,
    contradicted_trusted: List,
    knowledge_result: Dict = None,
):
    """
    Central AI Decision Engine.
    Returns:
        prediction
        confidence
        explanation
    """

    prediction = llm_verdict
    confidence = llm_confidence
    explanation = ""

    # ------------------------------------------
    # Rule 0: No supporting evidence
    # ------------------------------------------
    if (
        not knowledge_result
        and len(supported_trusted) == 0
        and len(contradicted_trusted) == 0
        and not fact_check_results
    ):
        return {
            "prediction": llm_verdict,
            "confidence": min(confidence, 60),
            "explanation": (
                "No trusted evidence or fact-check results were available. "
                "The verdict is based only on the language model and should be treated as provisional."
            ),
        }

    # ------------------------------------------
    # Rule 1: Verified Knowledge Base has highest priority
    # ------------------------------------------
    if knowledge_result and knowledge_result.get("found"):
        prediction = "REAL"
        confidence = max(confidence, 99)
        explanation = (
            f"Knowledge Base confirms the correct answer is "
            f"{knowledge_result.get('correct_answer')}"
        )

    # ------------------------------------------
    # Rule 2: Multiple trusted sources override the LLM
    # ------------------------------------------
    if len(supported_trusted) >= 2 and len(contradicted_trusted) == 0:
        prediction = "REAL"
        confidence = max(confidence, 95)
        explanation = (
            f"{len(supported_trusted)} trusted sources independently support this claim."
        )
    elif len(contradicted_trusted) >= 2 and len(supported_trusted) == 0:
        prediction = "FAKE"
        confidence = max(confidence, 95)
        explanation = (
            f"{len(contradicted_trusted)} trusted sources independently contradict this claim."
        )

    # ------------------------------------------
    # Calculate evidence scores
    # ------------------------------------------
    evidence = []

    # Knowledge Base
    if knowledge_result and knowledge_result.get("found"):
        evidence.append({
            "source": "Knowledge Base",
            "verdict": "REAL"
        })

    # LLM
    if llm_verdict:
        evidence.append({
            "source": "Groq",
            "verdict": llm_verdict
        })

    # Trusted Sources
    for _ in supported_trusted:
        evidence.append({
            "source": "Reuters",
            "verdict": "REAL"
        })

    for _ in contradicted_trusted:
        evidence.append({
            "source": "Reuters",
            "verdict": "FAKE"
        })

    scores = calculate_evidence_score(evidence)

    # ------------------------------------------
    # Final weighted decision
    # ------------------------------------------

    # If the LLM is highly confident, trust it unless trusted evidence strongly disagrees.
    if llm_confidence >= 95:

        if (
            llm_verdict == "FAKE"
            and scores["real_score"] <= scores["fake_score"]
        ):
            prediction = "FAKE"
            confidence = llm_confidence
            explanation = "High-confidence LLM verdict supported by available evidence."

        elif (
            llm_verdict == "REAL"
            and scores["fake_score"] <= scores["real_score"]
        ):
            prediction = "REAL"
            confidence = llm_confidence
            explanation = "High-confidence LLM verdict supported by available evidence."

    # Otherwise rely on evidence scores
    else:

        if scores["real_score"] > scores["fake_score"]:
            prediction = "REAL"
            confidence = min(
                99,
                max(confidence, scores["real_score"] // 4)
            )
            explanation = (
                f"{len(scores['real_sources'])} trusted evidence source(s) support this claim."
            )

        elif scores["fake_score"] > scores["real_score"]:
            prediction = "FAKE"
            confidence = min(
                99,
                max(confidence, scores["fake_score"] // 4)
            )
            explanation = (
                f"{len(scores['fake_sources'])} trusted evidence source(s) contradict this claim."
            )

    return {
        "prediction": prediction,
        "confidence": confidence,
        "explanation": explanation,
    }