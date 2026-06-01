# AI News Aggregator

A Python + Flask news intelligence platform that fetches real-time articles from NewsAPI, GNews API, and optionally The Guardian API. It summarizes articles, classifies categories, scores credibility, highlights suspicious items, and supports bookmarks.

## Features

- Real-time news collection from trusted sources and latest headlines
- Category filtering and search
- Groq LLM summarization, categorization, and credibility scoring for latest/trusted articles
- Dark mode responsive dashboard
- Bookmark/save news articles
- Auto-refresh every 10 minutes
- Secure API key handling via `.env`

## Project Structure

```
news_aggregator/
├── app.py
├── config.py
├── models.py
├── news_fetcher.py
├── llm_client.py
├── requirements.txt
├── .env.example
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## Setup Instructions

1. Clone or copy this folder into your workspace.
2. Change to the project folder:
   ```bash
   cd news_aggregator
   ```
3. Create a Python virtual environment and activate it:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Copy the example env file and add your API keys:
   ```bash
   copy .env.example .env
   ```
6. Open `.env` and fill in your keys for:
   - `NEWSAPI_KEY`
   - `GNEWS_API_KEY`
   - `GROQ_API_KEY`
   - optional `GUARDIAN_API_KEY`
7. Run the app:
   ```bash
   flask run
   ```
8. Open your browser at `http://127.0.0.1:5000`

## Notes

- API keys are consumed only server-side.
- If Guardian API is not configured, the app still works using NewsAPI and GNews.
- The Groq model is configurable through `GROQ_MODEL`.
- The `/news/latest` and `/news/trusted` endpoints prioritize updated headlines from trusted sources and enrich them via Groq.

