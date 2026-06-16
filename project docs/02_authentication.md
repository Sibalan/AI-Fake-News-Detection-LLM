# Module 02 — Authentication System

## Files
- `backend/routes/auth.py` — Authentication API endpoints
- `backend/models/user.py` — User & AdminLog database models

---

## Authentication Strategy

The system uses **two parallel authentication mechanisms**:

| Mechanism | Used For |
|---|---|
| JWT Token (Bearer) | API calls from JavaScript (AJAX) |
| Flask Session | Server-side page rendering / redirects |

On login, both a JWT token is issued and the user's ID is stored in the Flask session.

---

## `backend/routes/auth.py` — Auth Blueprint

**Blueprint prefix**: `/api/auth`

### Endpoints

#### `POST /api/auth/signup`

Register a new user account.

**Request Body**:
```json
{
  "username": "string (required, min 3 chars)",
  "email": "string (required, valid email)",
  "password": "string (required, min 6 chars)",
  "full_name": "string (optional)"
}
```

**Response (201)**:
```json
{
  "message": "Account created successfully",
  "user": { "id": 1, "username": "...", "email": "..." },
  "access_token": "JWT_TOKEN_STRING"
}
```

**Validations**:
- Username must be unique
- Email must be unique and valid format
- Password minimum 6 characters

---

#### `POST /api/auth/login`

Sign in with username/email and password.

**Request Body**:
```json
{
  "username": "string (username or email)",
  "password": "string"
}
```

**Response (200)**:
```json
{
  "message": "Login successful",
  "access_token": "JWT_TOKEN_STRING",
  "user": {
    "id": 1,
    "username": "...",
    "email": "...",
    "is_admin": false
  }
}
```

**Behavior**:
- Accepts either username or email in the `username` field
- Sets `session['user_id']` for server-side auth
- Returns 401 on invalid credentials
- Returns 403 if account is deactivated

---

#### `GET /api/auth/profile`

Get the current user's profile. Requires JWT token.

**Headers**: `Authorization: Bearer <token>`

**Response (200)**:
```json
{
  "user": {
    "id": 1,
    "username": "...",
    "email": "...",
    "full_name": "...",
    "is_admin": false,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

#### `PUT /api/auth/profile`

Update user profile fields. Requires JWT token.

**Request Body** (all optional):
```json
{
  "full_name": "string",
  "email": "string"
}
```

---

#### `POST /api/auth/change-password`

Change the authenticated user's password. Requires JWT token.

**Request Body**:
```json
{
  "current_password": "string",
  "new_password": "string (min 6 chars)"
}
```

---

## `backend/models/user.py` — User Model

### `User` Table

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment primary key |
| `username` | String(80) | Unique, indexed |
| `email` | String(120) | Unique, indexed |
| `password_hash` | String(255) | Bcrypt hashed password |
| `full_name` | String(200) | Optional display name |
| `is_admin` | Boolean | Admin privileges flag |
| `is_active` | Boolean | Account active/disabled |
| `created_at` | DateTime | Account creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

### Model Methods

```python
user.set_password("plain_text")     # Hashes and stores password
user.check_password("plain_text")   # Returns True/False
user.to_dict()                       # Serializes to JSON-safe dict
```

### Relationship

```python
# One user has many history entries
history = db.relationship('NewsHistory', backref='user', lazy=True)
```

---

### `AdminLog` Table

Tracks all administrative actions for audit purposes.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `admin_id` | Integer FK | References users.id |
| `action` | String(100) | Action type (e.g., "toggle_user") |
| `details` | Text | Action description |
| `ip_address` | String(45) | Admin's IP at time of action |
| `created_at` | DateTime | Timestamp of action |

---

## Password Security

Passwords are hashed using **bcrypt** via Flask-Bcrypt:

```python
from backend.models import bcrypt

# Hash
password_hash = bcrypt.generate_password_hash("plain").decode('utf-8')

# Verify
bcrypt.check_password_hash(password_hash, "plain")  # True/False
```

---

## JWT Token Usage

```javascript
// Store token after login
localStorage.setItem('access_token', response.access_token);

// Send with API requests
fetch('/api/auth/profile', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
});
```

Token expires after **24 hours** (`JWT_ACCESS_TOKEN_EXPIRES = 86400`).
