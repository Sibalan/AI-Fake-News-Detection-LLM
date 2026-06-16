# Module 10 — Admin Panel Module

## Files
- `backend/routes/admin.py` — Admin API endpoints
- `templates/admin_panel.html` — Admin UI
- `templates/admin/dashboard.html` — Admin analytics dashboard
- `backend/models/user.py` — AdminLog model

---

## Overview

The admin module provides privileged access to system-wide data and user management. All admin routes require the authenticated user to have `is_admin = True` in the database.

---

## Access Control

### Backend Guard

Every admin endpoint uses a custom decorator:

```python
from functools import wraps
from flask_jwt_extended import get_jwt_identity

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated
```

### Frontend Guard

The admin page checks admin status before rendering:

```javascript
const user = await getProfile();
if (!user.is_admin) {
    window.location.href = '/dashboard';
}
```

---

## Admin API Routes

**Blueprint prefix**: `/api/admin`  
**Auth required**: JWT + `is_admin = True`

---

### `GET /api/admin/dashboard`

Returns system-wide statistics.

**Response**:
```json
{
  "total_users": 150,
  "active_users": 148,
  "admin_count": 2,
  "total_predictions": 3420,
  "today_predictions": 45,
  "this_week_predictions": 312,
  "fake_count": 1990,
  "real_count": 1430,
  "fake_rate": 58.2,
  "method_breakdown": {
    "groq": 2100,
    "ollama": 850,
    "heuristic": 470
  },
  "top_categories": [
    { "category": "politics", "count": 1200 },
    { "category": "health", "count": 800 }
  ]
}
```

---

### `GET /api/admin/users`

Paginated list of all registered users.

**Query params**:
| Param | Default | Description |
|---|---|---|
| `page` | 1 | Page number |
| `per_page` | 20 | Items per page |
| `search` | — | Filter by username or email |
| `filter` | `all` | `all`, `active`, `inactive`, `admin` |

**Response**:
```json
{
  "users": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "is_admin": false,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "prediction_count": 23
    }
  ],
  "total": 150,
  "pages": 8,
  "current_page": 1
}
```

---

### `POST /api/admin/users/<id>/toggle`

Enable or disable a user account.

**Response**:
```json
{
  "message": "User deactivated successfully",
  "user_id": 5,
  "is_active": false
}
```

**Side effect**: Creates an `AdminLog` record:
```python
log = AdminLog(
    admin_id=current_admin_id,
    action="toggle_user",
    details=f"{'Activated' if new_status else 'Deactivated'} user {user.username}",
    ip_address=request.remote_addr
)
```

---

### `GET /api/admin/history`

All predictions across all users.

**Query params**:
| Param | Default | Description |
|---|---|---|
| `page` | 1 | Page number |
| `per_page` | 20 | Items per page |
| `filter` | `all` | `all`, `real`, `fake` |
| `user_id` | — | Filter by specific user |
| `method` | — | Filter by `groq`, `ollama`, `heuristic` |
| `from_date` | — | ISO date string |
| `to_date` | — | ISO date string |

---

### `GET /api/admin/stats/timeline`

Daily prediction counts for chart display.

**Query params**:
| Param | Default | Description |
|---|---|---|
| `days` | 30 | Number of days to include |

**Response**:
```json
{
  "timeline": [
    {
      "date": "2024-01-01",
      "total": 45,
      "fake": 28,
      "real": 17
    }
  ]
}
```

---

## Admin Panel UI (`admin_panel.html`)

Tabbed interface with four sections:

### Tab 1: Dashboard Stats

Stat cards showing:
- Total Users / Active Users
- Total Predictions Today
- Fake Rate percentage
- System method breakdown

Charts (Chart.js):
- **Doughnut**: REAL vs FAKE distribution
- **Bar**: Detection method usage (Groq / Ollama / Heuristic)

---

### Tab 2: User Management

Searchable, sortable user table:

| Column | Actions |
|---|---|
| ID | — |
| Username | — |
| Email | — |
| Joined Date | — |
| Total Analyses | — |
| Status | Toggle Active/Inactive button |
| Admin | Badge |

**Search** filters in real-time by username or email.

---

### Tab 3: All Predictions

System-wide prediction log table with:
- Date, User, Preview of text
- Prediction (REAL/FAKE badge)
- Confidence bar
- Method badge

Dropdown filters for prediction type and method.

---

### Tab 4: Analytics Timeline

Line chart showing daily REAL and FAKE counts over the last 30 days.

Date range selector (7 days / 30 days / 90 days).

---

## Admin Log (`AdminLog` Model)

Every admin action is automatically logged:

| Action Type | Trigger |
|---|---|
| `toggle_user` | Enable/disable user account |
| `view_dashboard` | Admin loads dashboard stats |
| `export_data` | Data export (if implemented) |

Query admin logs:
```python
logs = AdminLog.query.filter_by(admin_id=admin.id).order_by(
    AdminLog.created_at.desc()
).all()
```

---

## Creating an Admin User

### Via database seed (app startup)

```python
# In app.py — runs on first startup
admin = User(
    username='admin',
    email='admin@fakenews.ai',
    is_admin=True
)
admin.set_password('admin123')
```

### Via direct database update

```sql
UPDATE users SET is_admin = 1 WHERE username = 'yourusername';
```

### Via Flask shell

```python
flask shell
>>> from backend.models import db
>>> from backend.models.user import User
>>> user = User.query.filter_by(username='yourusername').first()
>>> user.is_admin = True
>>> db.session.commit()
```
