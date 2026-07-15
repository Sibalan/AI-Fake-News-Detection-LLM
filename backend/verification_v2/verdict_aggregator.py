from typing import List, Dict


def aggregate_verdicts(results: List[Dict]) -> Dict:
    """
    Combine verdicts from multiple evidence articles.
    """

    support = 0
    contradict = 0
    irrelevant = 0

    support_conf = []
    contradict_conf = []

    for result in results:

        verdict = result.get("verdict", "IRRELEVANT").upper()

        confidence = float(result.get("confidence", 0))

        if verdict == "SUPPORT":
            support += 1
            support_conf.append(confidence)

        elif verdict == "CONTRADICT":
            contradict += 1
            contradict_conf.append(confidence)

        else:
            irrelevant += 1

    # Majority decision
    if support > contradict:
        prediction = "REAL"

        confidence = (
            sum(support_conf) / len(support_conf)
            if support_conf else 75
        )

    elif contradict > support:
        prediction = "FAKE"

        confidence = (
            sum(contradict_conf) / len(contradict_conf)
            if contradict_conf else 75
        )

    else:
        prediction = "UNCERTAIN"
        confidence = 50

    return {
        "prediction": prediction,
        "confidence": round(confidence, 1),
        "support_count": support,
        "contradict_count": contradict,
        "irrelevant_count": irrelevant,
    }