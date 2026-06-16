# Module 12 — Test Suite

## Files
- `test_full.py` — Heuristic analysis test suite

---

## Overview

The test suite validates the **heuristic fallback analyzer** (`_smart_fallback` / `_heuristic_only_analysis` in `backend/ollama_client.py`) using a set of known true and false claims across multiple categories.

These tests verify that the pattern-based detection logic correctly identifies fake news indicators without relying on any external LLM service.

---

## Running the Tests

```bash
# From project root
python test_full.py
```

No external services required. Tests run entirely offline.

---

## Test Structure

Each test case is a tuple of `(claim, expected_verdict)`:

```python
test_cases = [
    ("The Earth orbits the Sun.", "REAL"),
    ("The Moon is made of cheese.", "FAKE"),
    ("NASA confirmed aliens visited Earth last week.", "FAKE"),
    ("The Supreme Court issued a ruling on data privacy.", "REAL"),
    ...
]
```

The test runner calls `_smart_fallback(claim)` for each case and checks if the returned `prediction` matches the expected verdict.

---

## Test Categories

### Space & Science Facts

| Claim | Expected |
|---|---|
| "The Earth orbits the Sun" | REAL |
| "The Moon is made of cheese" | FAKE |
| "Water is composed of hydrogen and oxygen" | REAL |
| "NASA confirmed alien life in 2023" | FAKE |
| "Scientists discovered a black hole in our solar system" | FAKE |

---

### General Knowledge Myths

| Claim | Expected |
|---|---|
| "Humans use only 10% of their brain" | FAKE |
| "Lightning never strikes the same place twice" | FAKE |
| "The Great Wall of China is visible from space" | FAKE |
| "Antibiotics are effective against viral infections" | FAKE |

---

### Indian Politics

| Claim | Expected |
|---|---|
| "The Indian Parliament passed a new budget bill" | REAL |
| "Prime Minister Modi secretly controls all media" | FAKE |
| "The Election Commission announced poll dates" | REAL |
| "BJP and Congress have secretly merged" | FAKE |

---

### Sports

| Claim | Expected |
|---|---|
| "Virat Kohli is a cricketer" | REAL |
| "MS Dhoni plays for the Indian football team" | FAKE |
| "The IPL tournament was held in 2023" | REAL |
| "Sachin Tendulkar won a boxing championship" | FAKE |

---

### International Figures

| Claim | Expected |
|---|---|
| "Elon Musk is the CEO of Tesla" | REAL |
| "Joe Biden is the Pope" | FAKE |
| "The United Nations issued a climate report" | REAL |
| "World leaders secretly planned a global lockdown" | FAKE |

---

### Health & Medicine

| Claim | Expected |
|---|---|
| "The WHO recommends regular handwashing" | REAL |
| "Vaccines cause autism according to scientists" | FAKE |
| "Regular exercise improves cardiovascular health" | REAL |
| "Drinking bleach cures COVID-19" | FAKE |

---

## Output Format

```
Running 45 test cases...

[PASS] "The Earth orbits the Sun." → REAL ✓
[PASS] "The Moon is made of cheese." → FAKE ✓
[FAIL] "Humans use only 10% of their brain" → Expected FAKE, got REAL
...

Results: 42/45 passed (93.3%)
Failed cases:
  - "Humans use only 10% of their brain"
  - ...
```

---

## What the Tests Validate

1. **Clickbait detection** — Sensational language correctly scores as FAKE
2. **Credible source recognition** — Articles citing Reuters/BBC/court rulings score as REAL
3. **Conspiracy language** — "Deep state", "secret plans" patterns trigger FAKE
4. **Factual statements** — Simple verifiable facts pass as REAL
5. **Known misinformation patterns** — Common myths are caught

---

## Limitations

- Tests only cover the **heuristic tier**, not Groq or Ollama responses
- Short, decontextualized claims are harder to classify than full articles
- The heuristic is designed for English-language news content
- Cultural/regional knowledge (Indian politics, IPL) may have lower accuracy on edge cases

---

## Adding New Test Cases

Append to the `test_cases` list in `test_full.py`:

```python
test_cases.append(
    ("Your news claim here.", "REAL")  # or "FAKE"
)
```

Test claims should be representative of real-world patterns, not just one-word prompts, to properly exercise the scoring logic.

---

## Integration Testing

For full end-to-end API testing, the following manual test flow is recommended:

```bash
# 1. Start the Flask app
python backend/app.py

# 2. Test health endpoint
curl http://localhost:5000/api/health

# 3. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'

# 4. Run a prediction (use token from login response)
curl -X POST http://localhost:5000/api/predict/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"text": "Scientists discovered that the moon is made of cheese according to unnamed sources."}'
```
