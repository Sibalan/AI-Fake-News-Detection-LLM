# Module 05 — API Routes Reference

## Files
- `backend/routes/auth.py` — `/api/auth/*`
- `backend/routes/predict.py` — `/api/predict/*`
- `backend/routes/history.py` — `/api/history/*`
- `backend/routes/admin.py` — `/api/admin/*`

---

## Base URL

```
http://localhost:5000
```

---

## Authentication

Most endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Get the token from `POST /api/auth/login`.

---

## Auth Routes — `/api/auth`

### `POST /api/auth/signup`

Create a new user account.

**Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secret123",
  "full_name": "John Doe"
}
```

**201 Created**:
```json
{
  "message": "Account created successfully",
  "access_token": "eyJ...",
  "user": { "id": 1, "username": "johndoe", "email": "john@example.com" }
}
```

**400 Bad Request**: Missing fields, weak password, invalid email  
**409 Conflict**: Username or email already exists

---

### `POST /api/auth/login`

```json
{ "username": "johndoe", "password": "secret123" }
```

**200 OK**:
```json
{
  "message": "Login successful",
  "access_token": "eyJ...",
  "user": { "id": 1, "username": "johndoe", "is_admin": false }
}
```

**401 Unauthorized**: Wrong password  
**403 Forbidden**: Account deactivated

---

### `GET /api/auth/profile` 🔒

Get authenticated user profile.

**200 OK**:
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_admin": false,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

### `PUT /api/auth/profile` 🔒

Update profile fields.

**Body** (all optional):
```json
{ "full_name": "Johnny Doe", "email": "newemail@example.com" }
```

---

### `POST /api/auth/change-password` 🔒

```json
{
  "current_password": "old123",
  "new_password": "new456"
}
```

**200 OK**: `{ "message": "Password changed successfully" }`  
**401**: Wrong current password

---

## Predict Routes — `/api/predict`

### `POST /api/predict/` 🔒

Analyze a news article for authenticity.

**Body**:
```json
{
  "text": "Your news article text here...",
  "source_url": "https://example.com/article",
  "source_type": "text"
}
```

**Processing**:
1. Validates text (minimum length check)
2. Records start time
3. Runs through Groq → Ollama → Heuristic pipeline
4. Performs NLP: sentiment analysis, keyword extraction, suspicious phrase detection
5. Saves to `NewsHistory` and `PredictionLog`
6. Returns full analysis

**200 OK**:
```json
{
  "prediction": "FAKE",
  "confidence": 0.87,
  "explanation": "The article uses several clickbait phrases...",
  "sentiment": "Negative",
  "sentiment_score": -0.45,
  "keywords": ["shocking", "truth", "government"],
  "suspicious_phrases": ["you won't believe", "deep state"],
  "processing_time": 2.34,
  "method": "groq",
  "fact_checks": [
    {
      "claim": "...",
      "rating": "False",
      "source": "FactCheck.org",
      "url": "https://..."
    }
  ],
  "category": "politics",
  "trusted_sources_found": [],
  "history_id": 42
}
```

**400**: Text too short or missing  
**500**: All detection methods failed

---

### `GET /api/predict/test`

Quick test endpoint, no auth required. Returns a sample fake analysis.

---

## History Routes — `/api/history`

### `GET /api/history/` 🔒

Get paginated prediction history for the current user.

**Query Params**:
| Param | Default | Description |
|---|---|---|
| `page` | 1 | Page number |
| `per_page` | 10 | Items per page (max 50) |
| `filter` | `all` | `all`, `real`, or `fake` |

**200 OK**:
```json
{
  "history": [ { ...news_history_item... } ],
  "total": 45,
  "pages": 5,
  "current_page": 1
}
```

---

### `GET /api/history/stats` 🔒

Get statistics for the authenticated user.

**200 OK**:
```json
{
  "total_analyses": 45,
  "fake_count": 28,
  "real_count": 17,
  "fake_percentage": 62.2,
  "avg_confidence": 0.81,
  "recent_activity": [...],
  "method_breakdown": {
    "groq": 30,
    "ollama": 10,
    "heuristic": 5
  }
}
```

---

### `GET /api/history/<id>` 🔒

Get a single history record by ID.

**200 OK**: Full `NewsHistory.to_dict()` object  
**403**: Record belongs to different user  
**404**: Record not found

---

### `DELETE /api/history/<id>` 🔒

Delete a specific history record.

---

### `DELETE /api/history/clear` 🔒

Delete all history for the authenticated user.

---

## Admin Routes — `/api/admin` 🔒 👑

All admin routes require `is_admin = True` on the user account.

### `GET /api/admin/dashboard`

System-wide statistics.

**200 OK**:
```json
{
  "total_users": 150,
  "active_users": 148,
  "total_predictions": 3420,
  "today_predictions": 45,
  "fake_rate": 58.3,
  "method_stats": { "groq": 2000, "ollama": 800, "heuristic": 620 }
}
```

---

### `GET /api/admin/users`

List all users with pagination.

**Query Params**: `page`, `per_page`, `search` (username/email)

**200 OK**:
```json
{
  "users": [ { ...user_dict, "prediction_count": 23 } ],
  "total": 150,
  "pages": 15
}
```

---

### `POST /api/admin/users/<id>/toggle`

Toggle a user's `is_active` status (enable/disable account).

**200 OK**:
```json
{ "message": "User deactivated", "is_active": false }
```

---

### `GET /api/admin/history`

All predictions across all users (not filtered by user).

**Query Params**: `page`, `per_page`, `filter` (`all`/`real`/`fake`), `user_id`

---

### `GET /api/admin/stats/timeline`

Prediction counts grouped by date for chart display.

**Query Params**: `days` (default 30)

**200 OK**:
```json
{
  "timeline": [
    { "date": "2024-01-01", "real": 12, "fake": 18, "total": 30 }
  ]
}
```

---

## System Routes

### `GET /api/health`

No auth required. Returns service health.

```json
{
  "status": "healthy",
  "database": "connected",
  "ollama": "available" | "unavailable",
  "groq": "configured" | "not configured"
}
```

### `GET /api/ollama/status`

Detailed Ollama server connection status.

---

## Error Response Format

All errors follow this format:

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

| HTTP Code | Meaning |
|---|---|
| 400 | Bad request / validation error |
| 401 | Not authenticated |
| 403 | Forbidden (not admin, or wrong user) |
| 404 | Resource not found |
| 409 | Conflict (duplicate username/email) |
| 500 | Internal server error |
