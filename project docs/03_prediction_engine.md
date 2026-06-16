# Module 03 — LLM Prediction Engine

## Files
- `backend/ollama_client.py` — Core detection engine (1,364 lines)
- `backend/groq_client.py` — Groq API client

---

## Detection Pipeline Overview

The prediction engine uses a **3-tier fallback architecture**:

```
Input: news_text
        │
        ▼
  ┌─────────────────────────────┐
  │  Tier 1: Groq API           │  (Llama 3.3 70B — cloud, fast)
  │  groq_client.analyze()      │
  └─────────────┬───────────────┘
                │ FAIL / no API key
                ▼
  ┌─────────────────────────────┐
  │  Tier 2: Ollama Phi-3 Mini  │  (local model, medium speed)
  │  _call_ollama()             │
  └─────────────┬───────────────┘
                │ FAIL / not running
                ▼
  ┌─────────────────────────────┐
  │  Tier 3: Heuristic Fallback │  (pattern matching, instant)
  │  _heuristic_only_analysis() │
  └─────────────────────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │  Enrichment Layer           │
  │  - Fact check API           │
  │  - Trusted source search    │
  │  - RSS feed lookup          │
  └─────────────────────────────┘
                │
                ▼
  Output: { prediction, confidence, explanation, fact_checks, category }
```

---

## `backend/ollama_client.py`

### Main Entry Function

```python
def analyze_with_phi3(news_text: str) -> dict
```

**Returns**:
```python
{
    "prediction": "REAL" | "FAKE",
    "confidence": 0.0 - 1.0,
    "explanation": "Detailed reasoning string",
    "fact_checks": [...],           # From Google Fact Check API
    "category": "sports" | "politics" | "health" | ...,
    "method": "groq" | "ollama" | "heuristic",
    "trusted_sources_found": [...], # Matching trusted articles
    "sentiment": "Positive" | "Negative" | "Neutral"
}
```

---

### Tier 1: Groq API Integration

Located in `groq_client.py`, called first in the pipeline.

```python
from groq_client import analyze_with_groq
result = analyze_with_groq(news_text)
```

- Uses `groq` Python SDK
- Model: `llama-3.3-70b-versatile`
- Returns `None` on failure (triggers fallback)
- Structured prompt extracts VERDICT and CONFIDENCE from LLM output

---

### Tier 2: Ollama Phi-3 Mini

```python
def _call_ollama(prompt: str) -> str
```

- Calls local Ollama server at `http://localhost:11434`
- Model: `phi3:mini`
- Uses `requests.post` to `/api/generate`
- Timeout: 30 seconds
- Returns raw text response or raises exception on failure

**Prompt Template**:
```
Analyze this news article and determine if it's REAL or FAKE.
Respond with exactly: VERDICT: [REAL/FAKE], CONFIDENCE: [0-100]%, 
EXPLANATION: [brief explanation]

News: {news_text}
```

---

### Tier 3: Heuristic Analysis

```python
def _heuristic_only_analysis(news_text: str) -> dict
```

Pattern-based scoring system that doesn't require any external service.

#### Fake News Indicators (negative score)

| Pattern | Score Penalty | Example |
|---|---|---|
| Clickbait phrases | -20 | "you won't believe", "shocking truth" |
| Conspiracy language | -25 | "deep state", "they don't want you to know" |
| Sensationalism | -15 | "BREAKING", "EXCLUSIVE BOMBSHELL" |
| Vague sourcing | -10 | "sources say", "unnamed officials" |
| Exaggeration | -10 | "100% proof", "absolutely confirms" |
| Emotional manipulation | -15 | "outrageous", "disgusting betrayal" |
| Excessive punctuation | -5 | Multiple `!!!` or `???` |
| All-caps words | -5 | More than 3 ALL-CAPS words |

#### Real News Indicators (positive score)

| Pattern | Score Boost | Example |
|---|---|---|
| Credible source citations | +25 | "Reuters reports", "according to BBC" |
| Peer-reviewed references | +20 | "study published in Nature" |
| Official statements | +20 | "government announced", "court ruled" |
| Law enforcement | +15 | "police confirmed", "FBI investigation" |
| Specific data/statistics | +10 | "GDP grew by 3.2%" |
| Named officials | +10 | "Prime Minister stated" |

#### Category Detection

The heuristic also identifies the article category based on keyword matching:

```python
categories = {
    "sports": ["cricket", "football", "IPL", "match", "tournament"],
    "politics": ["parliament", "election", "minister", "BJP", "Congress"],
    "health": ["vaccine", "hospital", "WHO", "disease", "treatment"],
    "finance": ["rupee", "stock market", "RBI", "inflation", "GDP"],
    "science": ["research", "NASA", "experiment", "discovery"],
    "education": ["university", "exam", "CBSE", "scholarship"]
}
```

#### Confidence Calculation

```python
# Score range: -100 to +100
# Mapped to confidence: 50% to 99%
confidence = min(99, max(50, 50 + abs(score) * 0.49))
prediction = "FAKE" if score < 0 else "REAL"
```

---

### Enrichment: Fact Checking

```python
def _fact_check_google(query: str) -> list
```

- Calls Google Fact Check Tools API
- Returns list of fact-check results with:
  - `claim`: The claim being checked
  - `rating`: Fact-check verdict (e.g., "False", "Misleading")
  - `source`: Fact-checking organization
  - `url`: Link to full fact-check article

---

### Enrichment: Trusted Source Search

```python
def _search_trusted_sources(query: str) -> list
```

Searches these trusted news domains:
- `bbc.com`, `reuters.com`, `apnews.com`
- `thehindu.com`, `ndtv.com`, `indianexpress.com`
- `timesofindia.com`, `hindustantimes.com`
- `aljazeera.com`, `theguardian.com`

Returns matching articles with title, URL, and source name.

---

## `backend/groq_client.py`

### Function

```python
def analyze_with_groq(news_text: str) -> dict | None
```

**Configuration**:
```python
from groq import Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
model = "llama-3.3-70b-versatile"
```

**Returns `None` when**:
- `GROQ_API_KEY` is not set
- API call fails or times out
- Response parsing fails

**Parsed Output**:
```python
{
    "prediction": "REAL" | "FAKE",
    "confidence": float,          # 0.0 to 1.0
    "explanation": str,
    "method": "groq"
}
```

---

## Performance Notes

| Method | Avg Speed | Accuracy | Requires |
|---|---|---|---|
| Groq (Llama 3.3 70B) | ~2-4 sec | High | GROQ_API_KEY |
| Ollama Phi-3 Mini | ~10-30 sec | Medium-High | Local Ollama server |
| Heuristic Fallback | <0.1 sec | Medium | Nothing |
