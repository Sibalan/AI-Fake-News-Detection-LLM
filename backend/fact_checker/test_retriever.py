from claim_extractor import extract_claim
from evidence_retriever import retrieve_evidence

claim = extract_claim("MS Dhoni is a football player")

results = retrieve_evidence(claim)

print()

print("Evidence Found:", len(results))

print()

for r in results:
    print(r)