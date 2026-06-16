# AI Fake News Detector — Project Overview

## Project Summary

An AI-powered fake news detection system that uses Large Language Models (LLMs) to analyze and classify news articles as **REAL** or **FAKE**. The system leverages a multi-tier AI pipeline combining cloud-based LLMs (Groq API), local models (Ollama Phi-3), and pattern-based heuristics as fallback.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Flask 3.0 |
| ORM | Flask-SQLAlchemy |
| Authentication | Flask-JWT-Extended + Flask-Bcrypt |
| Primary AI | Groq API (Llama 3.3 70B) |
| Secondary AI | Ollama (Phi-3 Mini, local) |
| Fallback AI | Heuristic pattern matching |
| NLP | NLTK, TextBlob |
| Database | SQLite (default) / MySQL |
| Frontend | Jinja2 templates + Tailwind CSS |
| Web Scraping | BeautifulSoup4, feedparser |

---

## Project Structure

```
AI_Fake_News_Detector_using_LLM/
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── config.py               # App configuration
│   ├── ollama_client.py        # Core LLM detection engine
│   ├── groq_client.py          # Groq API client
│   ├── models/
│   │   ├── __init__.py         # DB, JWT, Bcrypt initialization
│   │   ├── user.py             # User & AdminLog models
│   │   ├── news.py             # NewsHistory & Dataset models
│   │   └── prediction.py      # PredictionLog model
│   ├── routes/
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── predict.py          # Prediction endpoints
│   │   ├── history.py          # History endpoints
│   │   └── admin.py            # Admin endpoints
│   ├── ml/
│   │   └── preprocess.py       # Text preprocessing pipeline
│   └── utils/
│       ├── helpers.py          # Sentiment, suspicious phrase detection
│       └── news_api.py         # NewsAPI.org integration
├── database/
│   ├── schema.sql              # Database schema
│   └── app.db                  # SQLite database file
├── news_aggregator/
│   └── app.py                  # Standalone news aggregator app
├── static/
│   ├── css/style.css           # Custom styles + Tailwind
│   ├── js/api.js               # API helper with JWT
│   ├── js/main.js              # General page functionality
│   └── js/dashboard.js        # Dashboard interactions
├── templates/
│   ├── base.html               # Base layout template
│   ├── index.html              # Landing page
│   ├── login.html              # Login form
│   ├── signup.html             # Registration form
│   ├── dashboard.html          # User dashboard
│   ├── detect.html             # News analysis page
│   ├── history.html            # Prediction history
│   ├── about.html              # About page
│   ├── contact.html            # Contact form
│   ├── change_password.html    # Password change form
│   ├── admin_panel.html        # Admin interface
│   ├── admin/dashboard.html    # Admin analytics dashboard
│   └── components/
│       ├── navbar.html         # Navigation component
│       └── footer.html         # Footer component
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
├── test_full.py                # Heuristic analysis test suite
└── README.md
```

---

## Core Workflow

```
User submits news text
        │
        ▼
Groq API (Llama 3.3 70B) ──── success ──▶ Return result
        │
      failed
        │
        ▼
Ollama Phi-3 Mini (local) ──── success ──▶ Return result
        │
      failed
        │
        ▼
Heuristic Fallback Analysis ──────────▶ Return result
        │
        ▼
Fact Check + Trusted Source Search
        │
        ▼
Sentiment Analysis + Keyword Extraction
        │
        ▼
Save to NewsHistory + PredictionLog
        │
        ▼
Return: prediction, confidence, explanation, keywords, fact_checks
```

---

## Default Users

| Username | Password | Role |
|---|---|---|
| admin | admin123 | Administrator |
| demo | demo123 | Regular user |

---

## Module Documentation Index

| File | Module |
|---|---|
| [01_backend_core.md](01_backend_core.md) | Flask App & Configuration |
| [02_authentication.md](02_authentication.md) | Authentication System |
| [03_prediction_engine.md](03_prediction_engine.md) | LLM Prediction Engine |
| [04_database_models.md](04_database_models.md) | Database Models & Schema |
| [05_api_routes.md](05_api_routes.md) | API Endpoints Reference |
| [06_frontend_templates.md](06_frontend_templates.md) | Frontend Templates |
| [07_static_assets.md](07_static_assets.md) | Static Assets (CSS/JS) |
| [08_ml_utilities.md](08_ml_utilities.md) | ML & NLP Utilities |
| [09_news_aggregator.md](09_news_aggregator.md) | News Aggregator Module |
| [10_admin_module.md](10_admin_module.md) | Admin Panel Module |
| [11_configuration.md](11_configuration.md) | Configuration & Environment |
| [12_testing.md](12_testing.md) | Test Suite |
