from claim_extractor import extract_claim
from evidence_retriever import retrieve_evidence
from evidence_filter import filter_evidence
from llm_reasoner import reason_over_evidence
from verdict_engine import combine_verdicts

claim = extract_claim("MS Dhoni is a football player")

evidence = retrieve_evidence(claim)

filtered = filter_evidence(claim, evidence)

results = reason_over_evidence(claim, filtered)

final = combine_verdicts(results)

print("\n========== FINAL VERDICT ==========\n")

print(final)