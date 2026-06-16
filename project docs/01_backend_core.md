# Module 01 — Backend Core (Flask App & Configuration)

## Files
- `backend/app.py` — Application entry point
- `backend/config.py` — Configuration class

---

## `backend/app.py` — Flask Application Entry Point

### Purpose
Creates and configures the Flask application, registers all blueprints, initializes the database, sets up default users, and serves HTML pages.

### Initialization Sequence

```python
app = Flask(__name__)
app.config.from_object(Config)

# Extensions
db.init_app(app)
bcrypt.init_app(app)
jwt.init_app(app)
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(predict_bp, url_prefix='/api/predict')
app.register_blueprint(history_bp, url_prefix='/api/history')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
```

### Page Routes (HTML)

| Route | Template | Auth Required |
|---|---|---|
| `GET /` | `index.html` | No |
| `GET /login` | `login.html` | No |
| `GET /signup` | `signup.html` | No |
| `GET /dashboard` | `dashboard.html` | Session check |
| `GET /detect` | `detect.html` | Session check |
| `GET /history` | `history.html` | Session check |
| `GET /about` | `about.html` | No |
| `GET /contact` | `contact.html` | No |
| `GET /change-password` | `change_password.html` | Session check |
| `GET /admin` | `admin_panel.html` | Admin session |

### System API Routes

| Route | Description |
|---|---|
| `GET /api/health` | Health check, returns Ollama + DB status |
| `GET /api/ollama/status` | Detailed Ollama connection status |
| `GET /api/predict/test` | Quick test prediction endpoint |

### Default User Creation

On first startup, creates two seeded accounts if they don't exist:

```python
# Admin user
admin = User(username='admin', email='admin@fakenews.ai', is_admin=True)
admin.set_password('admin123')

# Demo user
demo = User(username='demo', email='demo@fakenews.ai')
demo.set_password('demo123')
```

### Error Handlers

| Code | Response |
|---|---|
| 404 | JSON `{"error": "Not found"}` |
| 500 | JSON `{"error": "Internal server error"}` |

---

## `backend/config.py` — Application Configuration

### Configuration Values

| Key | Default | Description |
|---|---|---|
| `SECRET_KEY` | From `.env` | Flask session secret |
| `JWT_SECRET_KEY` | From `.env` | JWT signing key |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///database/app.db` | Database connection |
| `JWT_ACCESS_TOKEN_EXPIRES` | `86400` (24 hours) | Token lifetime |
| `MAX_CONTENT_LENGTH` | `16 * 1024 * 1024` (16 MB) | Max upload size |
| `UPLOAD_FOLDER` | `uploads/` | File upload directory |
| `MODEL_PATH` | `models/` | ML model directory |

### Config Class

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///' + os.path.join(basedir, '..', 'database', 'app.db')
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=86400)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
```

---

## Running the App

```bash
# Development
cd backend
python app.py

# Production (gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Server starts at: `http://localhost:5000`

---

## Dependencies

```
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
Flask-JWT-Extended==4.6.0
Flask-Bcrypt==1.0.1
python-dotenv==1.0.0
gunicorn==21.2.0
Werkzeug==3.0.1
```
