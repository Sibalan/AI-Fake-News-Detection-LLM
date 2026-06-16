# Module 09 — News Aggregator

## Files
- `news_aggregator/app.py` — Standalone Flask application

---

## Overview

The news aggregator is a **separate Flask application** that runs independently from the main fake news detector. It fetches news from multiple external APIs, applies AI-powered summarization via Groq LLM, and presents articles organized by category and credibility.

**Port**: Runs on a different port from the main app (configurable).

---

## Application Structure

```
news_aggregator/
├── app.py              # Main application
├── templates/          # Aggregator-specific templates
└── news_aggregator.db  # Separate SQLite database
```

---

## News Sources

### Primary APIs

| API | Purpose | Free Tier |
|---|---|---|
| [NewsAPI.org](https://newsapi.org) | General news search | 100 req/day |
| [GNews API](https://gnews.io) | Alternative news source | 100 req/day |
| [The Guardian API](https://open-platform.theguardian.com) | Quality journalism | 500 req/day |

### Configuration

```python
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
GUARDIAN_API_KEY = os.environ.get("GUARDIAN_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
```

---

## Routes

### `GET /`

Home page displaying available news categories.

**Template**: `news_aggregator/templates/index.html`

**Categories available**:
- Technology
- Politics
- Sports
- Health
- Science
- Business
- Entertainment

---

### `GET /news/latest`

Fetches latest news from all configured APIs and returns with AI-generated summaries.

**Process**:
1. Calls NewsAPI `/everything` with recent date filter
2. Calls GNews `/search` for top headlines
3. Merges and deduplicates articles by title similarity
4. For each article, calls Groq LLM to generate a 2-sentence summary
5. Returns articles sorted by publication date

**Response format**:
```json
{
  "articles": [
    {
      "title": "Article headline",
      "source": "BBC News",
      "url": "https://...",
      "published_at": "2024-01-01T12:00:00Z",
      "summary": "AI-generated 2-sentence summary...",
      "category": "technology",
      "credibility_score": 0.85
    }
  ],
  "total": 25,
  "fetched_at": "2024-01-01T12:05:00Z"
}
```

---

### `GET /news/trusted`

Returns news only from pre-approved high-credibility sources.

**Trusted sources list**:
```python
TRUSTED_SOURCES = [
    "bbc-news", "reuters", "associated-press",
    "the-hindu", "ndtv", "the-guardian",
    "al-jazeera-english", "bloomberg"
]
```

Filters the NewsAPI results to only include these sources before returning.

---

## AI Integration (Groq LLM)

### Summarization

For each article, sends a prompt to Groq (Llama 3.3 70B):

```python
prompt = f"""
Summarize the following news article in exactly 2 sentences.
Be factual and neutral. Do not add opinions.

Title: {article['title']}
Content: {article['content'][:500]}

Summary:
"""
```

### Credibility Scoring

Each article gets a credibility score (0.0 to 1.0) based on:

| Factor | Weight |
|---|---|
| Source in trusted list | +0.4 |
| Article has full content | +0.2 |
| Published within 24 hours | +0.1 |
| No clickbait title patterns | +0.2 |
| Has author byline | +0.1 |

---

## Auto-Refresh

The app caches fetched articles and refreshes every **10 minutes** to stay current without hitting API rate limits:

```python
CACHE_TTL = 600  # 10 minutes in seconds

def get_cached_or_fetch(category):
    cached = cache.get(category)
    if cached and time.time() - cached['timestamp'] < CACHE_TTL:
        return cached['data']
    fresh = fetch_from_apis(category)
    cache[category] = {'data': fresh, 'timestamp': time.time()}
    return fresh
```

---

## Separate Database

The aggregator uses its own SQLite database (`news_aggregator.db`) with:

| Table | Purpose |
|---|---|
| `articles` | Cached fetched articles |
| `bookmarks` | User-saved articles |
| `categories` | Category configuration |

This keeps it fully decoupled from the main app's `app.db`.

---

## Running the Aggregator

```bash
cd news_aggregator
python app.py
```

Runs on `http://localhost:5001` (or configured port) independently of the main app.

---

## Environment Variables Required

```env
NEWS_API_KEY=your_newsapi_key
GNEWS_API_KEY=your_gnews_key
GUARDIAN_API_KEY=your_guardian_key
GROQ_API_KEY=your_groq_key   # Shared with main app
```
