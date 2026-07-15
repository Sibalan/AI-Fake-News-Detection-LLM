import requests

print("Testing Ollama...")

r = requests.get("http://localhost:11434/api/tags", timeout=10)

print(r.status_code)

print(r.text[:200])

from claim_extractor import extract_claim
from evidence_retriever import retrieve_evidence
from evidence_filter import filter_evidence
from llm_reasoner import reason_over_evidence


claim = extract_claim("MS Dhoni is a football player")

print("Claim:")
print(claim)

print()

evidence = retrieve_evidence(claim)

print("Retrieved:", len(evidence))

filtered = filter_evidence(claim, evidence)

print("Filtered:", len(filtered))

print()

results = reason_over_evidence(claim, filtered)

for i, result in enumerate(results, start=1):

    print("=" * 60)

    print("Evidence", i)

    print(result["article"]["title"])

    print()

    print("Verdict:", result["verdict"])

    print("Reason:", result["reason"])

    print()

    print(result["raw"])