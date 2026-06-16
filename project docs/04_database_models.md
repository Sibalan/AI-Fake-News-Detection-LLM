# Module 04 — Database Models & Schema

## Files
- `backend/models/__init__.py` — Extensions initialization
- `backend/models/user.py` — User & AdminLog models
- `backend/models/news.py` — NewsHistory & Dataset models
- `backend/models/prediction.py` — PredictionLog model
- `database/schema.sql` — Raw SQL schema
- `database/app.db` — SQLite database file

---

## Extensions Initialization (`models/__init__.py`)

```python
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
```

These three extension instances are imported throughout the app via:
```python
from backend.models import db, bcrypt, jwt
```

---

## Database Schema Overview

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│    users     │──1:N──│  news_history    │       │  prediction_logs │
│──────────────│       │──────────────────│       │──────────────────│
│ id           │       │ id               │       │ id               │
│ username     │       │ user_id (FK)     │       │ user_id (FK)     │
│ email        │       │ news_text        │       │ news_text (100)  │
│ password_hash│       │ prediction       │       │ prediction       │
│ full_name    │       │ confidence       │       │ confidence       │
│ is_admin     │       │ explanation      │       │ method           │
│ is_active    │       │ sentiment        │       │ processing_time  │
│ created_at   │       │ sentiment_score  │       │ ip_address       │
│ updated_at   │       │ keywords         │       │ created_at       │
└──────────────┘       │ suspicious_phrases│      └──────────────────┘
        │              │ source_url       │
        │1:N           │ processing_time  │       ┌──────────────────┐
        ▼              │ method           │       │   admin_logs     │
┌──────────────┐       │ source_type      │       │──────────────────│
│  admin_logs  │       │ created_at       │       │ id               │
│──────────────│       └──────────────────┘       │ admin_id (FK)    │
│ id           │                                  │ action           │
│ admin_id (FK)│       ┌──────────────────┐       │ details          │
│ action       │       │    datasets      │       │ ip_address       │
│ details      │       │──────────────────│       │ created_at       │
│ ip_address   │       │ id               │       └──────────────────┘
│ created_at   │       │ name             │
└──────────────┘       │ description      │
                       │ file_path        │
                       │ total_samples    │
                       │ is_active        │
                       └──────────────────┘
```

---

## `User` Model (`models/user.py`)

### Columns

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, auto | Primary key |
| `username` | String(80) | Unique, Not Null | Login name |
| `email` | String(120) | Unique, Not Null | Email address |
| `password_hash` | String(255) | Not Null | Bcrypt hash |
| `full_name` | String(200) | Nullable | Display name |
| `is_admin` | Boolean | Default False | Admin flag |
| `is_active` | Boolean | Default True | Account status |
| `created_at` | DateTime | Default now | Registration time |
| `updated_at` | DateTime | Auto update | Last modified time |

### Methods

```python
user.set_password("password")    # Bcrypt hash + store
user.check_password("password")  # True/False comparison
user.to_dict()                    # Returns JSON-serializable dict
```

### Indexes

```sql
CREATE INDEX ix_user_email ON users (email);
CREATE INDEX ix_user_username ON users (username);
CREATE INDEX ix_user_is_admin ON users (is_admin);
```

---

## `AdminLog` Model (`models/user.py`)

Audit trail for all admin actions.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `admin_id` | Integer FK | References `users.id` |
| `action` | String(100) | Action type string |
| `details` | Text | Human-readable description |
| `ip_address` | String(45) | Admin IP (IPv6 compatible) |
| `created_at` | DateTime | UTC timestamp |

---

## `NewsHistory` Model (`models/news.py`)

Full record of every prediction made by a user.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `user_id` | Integer FK | References `users.id` |
| `news_text` | Text | Full article text |
| `prediction` | String(10) | `"REAL"` or `"FAKE"` |
| `confidence` | Float | 0.0 to 1.0 |
| `explanation` | Text | LLM/heuristic reasoning |
| `sentiment` | String(20) | `"Positive"` / `"Negative"` / `"Neutral"` |
| `sentiment_score` | Float | TextBlob polarity score |
| `keywords` | Text | JSON array of top keywords |
| `suspicious_phrases` | Text | JSON array of detected phrases |
| `source_url` | String(500) | Optional article URL |
| `processing_time` | Float | Analysis duration (seconds) |
| `method` | String(20) | `"groq"` / `"ollama"` / `"heuristic"` |
| `source_type` | String(50) | e.g., `"text"`, `"url"` |
| `created_at` | DateTime | Prediction timestamp |

### `to_dict()` Output

```python
{
    "id": 1,
    "news_text": "...",
    "prediction": "FAKE",
    "confidence": 0.85,
    "explanation": "...",
    "sentiment": "Negative",
    "keywords": ["keyword1", "keyword2"],
    "suspicious_phrases": ["phrase1"],
    "created_at": "2024-01-01T12:00:00"
}
```

---

## `Dataset` Model (`models/news.py`)

Reference table for training/test datasets.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(200) | Dataset name |
| `description` | Text | Description |
| `file_path` | String(500) | Path to data file |
| `total_samples` | Integer | Number of records |
| `is_active` | Boolean | Currently in use |

---

## `PredictionLog` Model (`models/prediction.py`)

Lightweight audit log, stores truncated text to save space.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `user_id` | Integer FK | References `users.id` (nullable) |
| `news_text` | String(100) | First 100 chars of article |
| `prediction` | String(10) | `"REAL"` or `"FAKE"` |
| `confidence` | Float | Confidence score |
| `method` | String(20) | Detection method used |
| `processing_time` | Float | Time taken (seconds) |
| `ip_address` | String(45) | Requester's IP |
| `created_at` | DateTime | Log timestamp |

---

## Database Initialization

```python
# In app.py
with app.app_context():
    db.create_all()  # Creates all tables from models
```

Tables are created automatically from SQLAlchemy models on startup if they don't exist.

---

## Switching to MySQL

Change `DATABASE_URL` in `.env`:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost/fakenews_db
```

Install driver:
```bash
pip install PyMySQL cryptography
```
