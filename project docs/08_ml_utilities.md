# Module 08 — ML & NLP Utilities

## Files
- `backend/ml/preprocess.py` — Text preprocessing pipeline
- `backend/utils/helpers.py` — Sentiment analysis & suspicious phrase detection
- `backend/utils/news_api.py` — NewsAPI.org integration

---

## `backend/ml/preprocess.py` — Text Preprocessing

Provides a pipeline to clean and tokenize news text before analysis.

### Pipeline

```
raw text
    │
    ▼
clean_text()        → removes URLs, HTML, special chars, numbers
    │
    ▼
tokenize()          → splits into word tokens (NLTK)
    │
    ▼
remove_stopwords()  → filters common English words
    │
    ▼
preprocess_text()   → returns { tokens, word_count, clean_text }
```

---

### `clean_text(text: str) -> str`

Applies regex transformations in sequence:

```python
# 1. Remove URLs
text = re.sub(r'http\S+|www\S+', '', text)

# 2. Remove HTML tags
text = re.sub(r'<[^>]+>', '', text)

# 3. Remove special characters (keep alphanumeric + spaces)
text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

# 4. Remove standalone numbers
text = re.sub(r'\b\d+\b', '', text)

# 5. Normalize whitespace
text = ' '.join(text.split())

return text.lower()
```

---

### `tokenize(text: str) -> list[str]`

Uses NLTK's `word_tokenize`:

```python
import nltk
from nltk.tokenize import word_tokenize

def tokenize(text: str) -> list:
    return word_tokenize(text.lower())
```

Requires NLTK `punkt` tokenizer data (downloaded on first use).

---

### `remove_stopwords(tokens: list) -> list`

Filters English stopwords using NLTK's stopword corpus:

```python
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))

def remove_stopwords(tokens: list) -> list:
    return [t for t in tokens if t not in stop_words and len(t) > 2]
```

---

### `preprocess_text(text: str) -> dict`

Full pipeline function returning processed result:

```python
def preprocess_text(text: str) -> dict:
    clean = clean_text(text)
    tokens = tokenize(clean)
    filtered = remove_stopwords(tokens)
    return {
        "tokens": filtered,
        "word_count": len(filtered),
        "clean_text": clean
    }
```

---

### `extract_keywords(text: str, n: int = 10) -> list[str]`

Returns top N most frequent non-stopword tokens:

```python
def extract_keywords(text: str, n: int = 10) -> list:
    result = preprocess_text(text)
    freq = Counter(result["tokens"])
    return [word for word, _ in freq.most_common(n)]
```

---

## `backend/utils/helpers.py` — Helper Functions

### `analyze_sentiment(text: str) -> dict`

Uses **TextBlob** for polarity analysis:

```python
from textblob import TextBlob

def analyze_sentiment(text: str) -> dict:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1.0 to +1.0

    if polarity > 0.1:
        label = "Positive"
    elif polarity < -0.1:
        label = "Negative"
    else:
        label = "Neutral"

    return {
        "sentiment": label,
        "score": round(polarity, 4)
    }
```

| Score Range | Label |
|---|---|
| > 0.1 | Positive |
| -0.1 to 0.1 | Neutral |
| < -0.1 | Negative |

---

### `find_suspicious_phrases(text: str) -> list[str]`

Scans text using regex patterns associated with misinformation:

```python
SUSPICIOUS_PATTERNS = [
    # Clickbait
    r"you won't believe",
    r"shocking (truth|secret|revelation)",
    r"what (they|media) don't want you to know",

    # Conspiracy
    r"deep state",
    r"new world order",
    r"they're hiding",
    r"mainstream media won't report",

    # Sensationalism
    r"BREAKING[:\s]",
    r"EXCLUSIVE[:\s]",
    r"BOMBSHELL",

    # Vague sourcing
    r"sources (say|claim|reveal)",
    r"unnamed (official|source)",
    r"according to insiders",

    # Emotional manipulation
    r"outrag(e|eous|ing)",
    r"disgusting betrayal",
    r"absolute proof",
    r"100% confirmed",
]

def find_suspicious_phrases(text: str) -> list:
    found = []
    text_lower = text.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            found.append(pattern.replace(r'\b', '').strip())
    return found
```

---

### `calculate_confidence_from_score(score: float) -> float`

Converts a raw heuristic score (−100 to +100) to a confidence percentage (0.5 to 0.99):

```python
def calculate_confidence_from_score(score: float) -> float:
    normalized = min(99, max(50, 50 + abs(score) * 0.49))
    return round(normalized / 100, 4)
```

| Score | Confidence |
|---|---|
| 0 | 0.50 (50%) |
| ±50 | ~0.75 (75%) |
| ±100 | 0.99 (99%) |

---

## `backend/utils/news_api.py` — NewsAPI Integration

Fetches real-time news from [NewsAPI.org](https://newsapi.org) for context matching.

### Configuration

```python
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
BASE_URL = "https://newsapi.org/v2"
```

### `fetch_related_news(query: str, limit: int = 5) -> list`

```python
def fetch_related_news(query: str, limit: int = 5) -> list:
    params = {
        "q": query[:100],           # Truncate long queries
        "apiKey": NEWS_API_KEY,
        "pageSize": limit,
        "language": "en",
        "sortBy": "relevancy"
    }
    response = requests.get(f"{BASE_URL}/everything", params=params, timeout=5)
    articles = response.json().get("articles", [])
    return [
        {
            "title": a["title"],
            "source": a["source"]["name"],
            "url": a["url"],
            "published": a["publishedAt"]
        }
        for a in articles
    ]
```

Returns empty list if `NEWS_API_KEY` is not configured.

---

## NLTK Data Requirements

These NLTK datasets must be downloaded before first use:

```python
import nltk
nltk.download('punkt')          # Tokenizer
nltk.download('stopwords')      # Stopword list
nltk.download('averaged_perceptron_tagger')  # POS tagger (optional)
```

The `app.py` startup sequence triggers these downloads if missing.

---

## Dependencies

```
nltk==3.8.1
textblob==0.17.1
beautifulsoup4==4.12.2
lxml==4.9.4
requests==2.31.0
feedparser==6.0.11
```
