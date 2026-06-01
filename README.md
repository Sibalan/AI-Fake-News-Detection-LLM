# AI-Based Fake News Detection System

<div align="center">
  <img src="https://img.shields.io/badge/Flask-3.0-000?logo=flask" alt="Flask" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" alt="React" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-3.3-06B6D4?logo=tailwindcss" alt="Tailwind" />
  <img src="https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql" alt="MySQL" />
  <img src="https://img.shields.io/badge/Ollama-Phi--3-6366F1?logo=ollama" alt="Ollama" />
  <br/>
  <strong>MCA Major Project | IV Semester | RV College of Engineering</strong>
</div>

## Overview

An intelligent AI-powered platform that detects fake news using **Microsoft Phi-3 LLM** running locally via **Ollama**. The system analyzes news content in real-time, providing predictions with confidence scores, AI-generated explanations, and detailed analytics through a modern, responsive web interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Tailwind)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │   Home   │ │Dashboard │ │  History │ │ Admin (Analytics)│  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬───────┘  │
│       └────────────┴────────────┴────────────────┘          │
│                       │  REST API (Axios)                    │
├─────────────────────────────────────────────────────────────┤
│                    Backend (Flask)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │   Auth   │ │ Predict  │ │  History │ │    Admin      │  │
│  │  Routes  │ │  Routes  │ │  Routes  │ │    Routes     │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬───────┘  │
│       └────────────┴────────────┴────────────────┘          │
│                         │ JWT Auth                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Ollama Phi-3 (Local LLM)                 │   │
│  │         http://localhost:11434/api/generate           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MySQL Database (XAMPP)                   │   │
│  │     users | news_history | prediction_logs           │   │
│  │     admin_logs | datasets                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Core Features
- **AI-Powered Detection**: Uses Microsoft Phi-3 LLM via local Ollama for privacy-preserving news analysis
- **Real-time Prediction**: Instant results with confidence scoring
- **AI Explanations**: Detailed natural language explanations for each prediction
- **Sentiment Analysis**: Understand the emotional tone of news content
- **Suspicious Pattern Detection**: Identifies clickbait, sensationalism, and manipulation markers
- **Keyword Extraction**: Automatic extraction of key terms from analyzed text

### User Features
- **User Authentication**: Secure signup/login with JWT tokens
- **Analysis Dashboard**: Clean interface for news input and result visualization
- **History Tracking**: Complete history with search, filter, and pagination
- **Visual Analytics**: Charts and graphs for prediction statistics
- **Responsive Design**: Fully functional on desktop, tablet, and mobile

### Admin Features
- **User Management**: View, search, and toggle user accounts
- **System Analytics**: Real-time vs fake distribution, prediction timelines
- **Dashboard Overview**: System health, total predictions, user statistics
- **Activity Monitoring**: Recent predictions and system logs

## Tech Stack

### Backend
- **Flask 3.0** - Python web framework
- **Flask-SQLAlchemy** - ORM for database operations
- **Flask-JWT-Extended** - Secure token-based authentication
- **Flask-Bcrypt** - Password hashing
- **Flask-CORS** - Cross-origin resource sharing
- **PyMySQL** - MySQL database driver

### Frontend
- **React 18** - UI library
- **Tailwind CSS 3.3** - Utility-first CSS framework
- **Recharts** - Charting library
- **Framer Motion** - Animations
- **React Router v6** - Client-side routing
- **React Hot Toast** - Notifications
- **React Icons** - Icon library
- **Axios** - HTTP client

### AI/ML
- **Ollama** - Local LLM server
- **Phi-3 Mini** - Microsoft's lightweight LLM
- **NLTK** - Natural Language Toolkit for text preprocessing
- **TextBlob** - Sentiment analysis

### Database
- **MySQL 8** via XAMPP

## Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8 (XAMPP)
- Ollama with Phi-3 model

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI_Fake_News_Detector
```

### 2. Database Setup
1. Start XAMPP and ensure MySQL is running
2. Open phpMyAdmin or MySQL CLI
3. Run the schema file:
```bash
mysql -u root < database/schema.sql
```

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run the backend
cd backend
python app.py
```

### 4. Install & Run Ollama
```bash
# Install Ollama from https://ollama.ai
# Pull Phi-3 model
ollama pull phi3:mini

# Ensure Ollama is running
ollama serve
```

### 5. Frontend Setup
```bash
cd frontend
npm install
npm start
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Demo User | demo | demo123 |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Create new account |
| POST | `/api/auth/login` | Sign in |
| GET | `/api/auth/profile` | Get user profile |
| PUT | `/api/auth/profile` | Update profile |
| POST | `/api/auth/change-password` | Change password |

### Prediction
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict/` | Analyze news text |

### History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history/` | Get user history |
| GET | `/api/history/stats` | Get user statistics |
| GET | `/api/history/<id>` | Get history detail |
| DELETE | `/api/history/<id>` | Delete history item |
| DELETE | `/api/history/clear` | Clear all history |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Admin dashboard data |
| GET | `/api/admin/users` | List all users |
| POST | `/api/admin/users/<id>/toggle` | Toggle user status |
| GET | `/api/admin/history` | All prediction history |
| GET | `/api/admin/stats/timeline` | Prediction timeline |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + Ollama status |
| GET | `/api/ollama/status` | Ollama server status |

## Project Structure

```
AI_Fake_News_Detector/
├── backend/
│   ├── app.py                    # Flask application entry point
│   ├── config.py                 # Configuration settings
│   ├── requirements.txt          # Python dependencies
│   ├── ollama_client.py          # Ollama Phi-3 integration
│   ├── models/
│   │   ├── __init__.py           # Database, bcrypt, JWT init
│   │   ├── user.py               # User & AdminLog models
│   │   ├── news.py              # NewsHistory & Dataset models
│   │   └── prediction.py         # PredictionLog model
│   ├── routes/
│   │   ├── auth.py               # Authentication routes
│   │   ├── predict.py            # Prediction routes
│   │   ├── history.py            # History routes
│   │   └── admin.py              # Admin routes
│   ├── ml/
│   │   └── preprocess.py         # NLP text preprocessing
│   └── utils/
│       └── helpers.py            # Utility functions
├── frontend/
│   ├── public/index.html
│   ├── src/
│   │   ├── App.js                # Main app with routing
│   │   ├── index.js              # Entry point
│   │   ├── index.css             # Tailwind + custom styles
│   │   ├── context/AuthContext.js # Auth state management
│   │   ├── services/api.js       # Axios API client
│   │   ├── components/
│   │   │   ├── Navbar.js         # Responsive navbar
│   │   │   └── Footer.js         # Site footer
│   │   └── pages/
│   │       ├── Home.js           # Landing page
│   │       ├── About.js          # Project info
│   │       ├── Dashboard.js      # Main prediction dashboard
│   │       ├── History.js        # Analysis history
│   │       ├── Login.js          # Sign in form
│   │       ├── Signup.js         # Register form
│   │       ├── Contact.js        # Contact page
│   │       ├── ChangePassword.js # Password change form
│   │       └── AdminDashboard.js # Admin panel
│   ├── package.json
│   ├── tailwind.config.js
│   └── postcss.config.js
├── database/
│   └── schema.sql                # MySQL database schema
├── static/assets/                 # Static assets
├── .env                          # Environment variables
├── .gitignore
└── README.md
```

## Deployment

### Backend (Render/Railway)
```bash
# Deploy Flask app using gunicorn
gunicorn backend.app:create_app() --workers 4 --bind 0.0.0.0:$PORT
```

### Frontend (Vercel/Netlify)
```bash
cd frontend
npm run build
# Deploy the build/ directory
```

### Environment Variables
| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key |
| `JWT_SECRET_KEY` | JWT signing key |
| `DATABASE_URL` | MySQL connection string |
| `OLLAMA_BASE_URL` | Ollama server URL |

## Accuracy & Limitations

- The system uses **Phi-3 Mini** LLM for analysis, which provides nuanced understanding of text
- Accuracy depends on the quality of the LLM's reasoning and training data
- The fallback analyzer uses heuristic pattern matching when Ollama is unavailable
- For best results, provide complete news articles (not just headlines)

## Acknowledgments

- **RV College of Engineering**, Department of Master of Computer Applications
- **Course**: MCA491P - Major Project, IV Semester
- **Technology**: Microsoft Phi-3, Ollama, Flask, React, Tailwind CSS

---

<div align="center">
  <p>Developed as MCA Major Project | RV College of Engineering</p>
  <p>Department of Master of Computer Applications | Bengaluru</p>
</div>
```
