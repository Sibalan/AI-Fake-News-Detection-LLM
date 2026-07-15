import re



def parse_response(text):
    """
    Parse the LLM response.
    """

    if not text:
        return "IRRELEVANT", "No response from model."

    verdict = "IRRELEVANT"

    upper = text.upper()

    if "SUPPORTS" in upper:
        verdict = "SUPPORTS"
    elif "CONTRADICTS" in upper:
        verdict = "CONTRADICTS"
    elif "IRRELEVANT" in upper:
        verdict = "IRRELEVANT"

    match = re.search(r"Reason\s*:\s*(.*)", text, re.I | re.S)

    if match:
        reason = match.group(1).strip()
    else:
        reason = text.strip()

    return verdict, reason


def reason_over_evidence(claim, evidence, llm_callback):
    """
    Ask the LLM whether each article supports or contradicts the claim.
    """

    results = []

    claim_text = claim["original_text"]

    for article in evidence:

        prompt = f"""
You are an expert fact checker.

Claim:
{claim_text}

Evidence Title:
{article.get("title", "")}

Evidence:
{article.get("summary", "")}

Reply ONLY in this format:

VERDICT: SUPPORTS

Reason:
...

OR

VERDICT: CONTRADICTS

Reason:
...

OR

VERDICT: IRRELEVANT

Reason:
...
"""

        print("\n================ PROMPT ================\n")
        print(prompt)

        response = llm_callback(prompt)

        print("\n================ RESPONSE ================\n")
        print(response)

        verdict, reason = parse_response(response)

        results.append(
            {
                "article": article,
                "verdict": verdict,
                "reason": reason,
                "raw": response,
            }
        )

    return results