# Module 11 — Configuration & Environment

## Files
- `.env` — Environment variables
- `backend/config.py` — Flask configuration class
- `requirements.txt` — Python dependencies

---

## `.env` — Environment Variables

Located at the project root. Loaded by `python-dotenv` at startup.

### All Variables

```env
# Flask
SECRET_KEY=rvce-mca-project-secret-key-2024-super-secure
FLASK_ENV=development
PORT=5000

# JWT
JWT_SECRET_KEY=jwt-secret-key-rvce-mca-2024-secure-token

# Database (leave blank to use SQLite default)
DATABASE_URL=

# Ollama (local LLM server)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini

# Groq API (cloud LLM - fast inference)
GROQ_API_KEY=gsk_your_groq_api_key_here

# NewsAPI (optional - for news context matching)
NEWS_API_KEY=

# GNews API (optional - used by news aggregator)
GNEWS_API_KEY=

# The Guardian API (optional - used by news aggregator)
GUARDIAN_API_KEY=

# Google Fact Check API (optional - for fact verification)
GOOGLE_FACT_CHECK_API_KEY=
```

---

## Variable Details

### `SECRET_KEY`
Flask's secret key for session signing and CSRF protection.  
**Required**: Yes  
**Production**: Must be changed to a random 32+ character string

### `JWT_SECRET_KEY`
Key used to sign JWT access tokens.  
**Required**: Yes  
**Production**: Must be changed and kept secret

### `FLASK_ENV`
Controls debug mode and error visibility.  
**Values**: `development` (verbose errors) or `production` (safe errors)  
**Production**: Must be set to `production`

### `PORT`
Port for the Flask server.  
**Default**: `5000`

### `DATABASE_URL`
SQLAlchemy connection string.  
**SQLite (default)**: Leave empty — uses `database/app.db`  
**MySQL**: `mysql+pymysql://user:password@host/dbname`  
**PostgreSQL**: `postgresql://user:password@host/dbname`

### `OLLAMA_BASE_URL`
URL to the local Ollama inference server.  
**Default**: `http://localhost:11434`  
**Required for Tier 2**: Ollama must be running with `phi3:mini` model

### `GROQ_API_KEY`
API key for Groq cloud LLM service (Llama 3.3 70B).  
**Get key**: [console.groq.com](https://console.groq.com)  
**Required for Tier 1**: Optional but strongly recommended for speed/quality

### `NEWS_API_KEY`
API key for NewsAPI.org.  
**Get key**: [newsapi.org](https://newsapi.org)  
**Optional**: Used for trusted source search enrichment

---

## `backend/config.py` — Config Class

```python
import os
from datetime import timedelta
from pathlib import Path

basedir = Path(__file__).parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'change-jwt-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + str(basedir.parent / 'database' / 'app.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_EXPIRES', 86400))
    )

    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = str(basedir / 'uploads')
    MODEL_PATH = str(basedir / 'models')

    # Ollama
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'phi3:mini')
```

---

## `requirements.txt` — Python Dependencies

```
# Web framework
Flask==3.0.0
Flask-CORS==4.0.0
Werkzeug==3.0.1
gunicorn==21.2.0

# Database
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.0
cryptography==41.0.7

# Authentication
Flask-JWT-Extended==4.6.0
Flask-Bcrypt==1.0.1

# Environment
python-dotenv==1.0.0

# HTTP
requests==2.31.0

# NLP
nltk==3.8.1
textblob==0.17.1

# Web scraping
beautifulsoup4==4.12.2
lxml==4.9.4
feedparser==6.0.11

# LLM
groq==0.9.0
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Post-install NLTK data

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## Environment Setup Guide

### 1. Clone and install

```bash
git clone <repo>
cd AI_Fake_News_Detector_using_LLM
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env   # Windows
# Edit .env with your keys
```

### 3. Set up Ollama (optional but recommended)

```bash
# Install Ollama from https://ollama.ai
ollama pull phi3:mini
ollama serve
```

### 4. Run the app

```bash
cd backend
python app.py
```

---

## Production Checklist

| Setting | Development | Production |
|---|---|---|
| `SECRET_KEY` | Any string | Random 32+ chars |
| `JWT_SECRET_KEY` | Any string | Random 32+ chars |
| `FLASK_ENV` | `development` | `production` |
| `DATABASE_URL` | SQLite | PostgreSQL/MySQL |
| `GROQ_API_KEY` | Optional | Recommended |
| Debug mode | On | Off |
| HTTPS | Optional | Required |
