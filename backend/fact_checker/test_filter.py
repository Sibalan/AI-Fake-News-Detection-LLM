from claim_extractor import extract_claim
from evidence_retriever import retrieve_evidence
from evidence_filter import filter_evidence

claim = extract_claim("MS Dhoni is a football player")

evidence = retrieve_evidence(claim)

filtered = filter_evidence(claim, evidence)

print()

print("Before:", len(evidence))

print("After:", len(filtered))

print()

for article in filtered:
    print(article["title"])