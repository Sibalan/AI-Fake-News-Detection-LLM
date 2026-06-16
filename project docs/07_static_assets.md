# Module 07 — Static Assets (CSS & JavaScript)

## Files
- `static/css/style.css` — Custom styles and Tailwind integration
- `static/js/api.js` — API helper functions with JWT support
- `static/js/main.js` — General page functionality
- `static/js/dashboard.js` — Dashboard-specific interactions
- `static/assets/` — Images and other media files

---

## `static/css/style.css` — Styling

### Approach

The project uses **Tailwind CSS** (loaded via CDN in `base.html`) for utility-first styling. `style.css` provides:
- Custom component styles that can't be covered by Tailwind utilities
- CSS animations and transitions
- Custom color variables
- Scrollbar styling
- Print styles

### Key Custom Styles

#### Result Badge Animations
```css
/* FAKE verdict — red pulsing badge */
.verdict-fake {
    animation: pulse-red 1.5s infinite;
}

/* REAL verdict — green solid badge */
.verdict-real {
    animation: fade-in 0.5s ease;
}
```

#### Confidence Bar
```css
.confidence-bar {
    transition: width 0.8s ease-in-out;
}
.confidence-fill-fake { background: linear-gradient(90deg, #ef4444, #dc2626); }
.confidence-fill-real { background: linear-gradient(90deg, #22c55e, #16a34a); }
```

#### Loading Spinner
```css
.spinner {
    border: 3px solid #f3f3f3;
    border-top-color: #3498db;
    animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

#### Keyword Chips
```css
.keyword-chip {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 9999px;
    background: #e0f2fe;
    color: #0369a1;
    font-size: 0.75rem;
}
.suspicious-chip {
    background: #fee2e2;
    color: #b91c1c;
}
```

---

## `static/js/api.js` — API Helper

Central module for all HTTP calls to the Flask backend.

### JWT Management

```javascript
const API = {
    getToken() {
        return localStorage.getItem('access_token');
    },

    setToken(token) {
        localStorage.setItem('access_token', token);
    },

    clearToken() {
        localStorage.removeItem('access_token');
    },

    isLoggedIn() {
        return !!this.getToken();
    }
};
```

### Request Helper

```javascript
async function apiRequest(endpoint, options = {}) {
    const token = API.getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers
    };

    const response = await fetch(endpoint, { ...options, headers });

    if (response.status === 401) {
        API.clearToken();
        window.location.href = '/login';
        return;
    }

    return response.json();
}
```

### Exported Functions

| Function | Endpoint | Description |
|---|---|---|
| `loginUser(username, password)` | `POST /api/auth/login` | Login + store token |
| `signupUser(data)` | `POST /api/auth/signup` | Register new user |
| `getProfile()` | `GET /api/auth/profile` | Fetch current user |
| `analyzeNews(text, url)` | `POST /api/predict/` | Run prediction |
| `getHistory(page, filter)` | `GET /api/history/` | Fetch history page |
| `getStats()` | `GET /api/history/stats` | User statistics |
| `deleteHistory(id)` | `DELETE /api/history/<id>` | Remove one record |
| `clearHistory()` | `DELETE /api/history/clear` | Remove all records |
| `changePassword(curr, new)` | `POST /api/auth/change-password` | Change password |

---

## `static/js/main.js` — General Page Functionality

Handles behaviors shared across multiple pages.

### Responsibilities

#### Mobile Navigation Toggle
```javascript
document.getElementById('menu-btn').addEventListener('click', () => {
    document.getElementById('mobile-menu').classList.toggle('hidden');
});
```

#### Auth State UI Updates
On every page load, checks login state and updates navbar:
- Shows/hides Login vs Logout button
- Shows/hides Dashboard link
- Shows/hides Admin link for admin users

#### Flash Message Auto-dismiss
```javascript
setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach(el => {
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 300);
    });
}, 3000);
```

#### Logout Handler
```javascript
document.getElementById('logout-btn')?.addEventListener('click', () => {
    API.clearToken();
    window.location.href = '/';
});
```

---

## `static/js/dashboard.js` — Dashboard Interactions

Handles all dynamic behavior on the `/dashboard` page.

### Page Load

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    await loadStats();        // Fetch and display stat cards
    await loadRecentHistory(); // Load last 5 predictions
    setupAnalysisForm();      // Wire up the analysis form
});
```

### `loadStats()`

Calls `GET /api/history/stats` and updates:
- Total analyses counter
- Fake/Real count cards
- Average confidence display
- Prediction method breakdown

### `setupAnalysisForm()`

Handles the main news analysis form:

```javascript
analysisForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = newsInput.value.trim();

    showLoadingState();       // Show spinner, disable button

    const result = await apiRequest('/api/predict/', {
        method: 'POST',
        body: JSON.stringify({ text })
    });

    hideLoadingState();
    displayResult(result);    // Render verdict, confidence, explanation
    await loadRecentHistory(); // Refresh history table
});
```

### `displayResult(result)`

Renders the analysis result section:

```javascript
function displayResult(result) {
    // Set verdict badge color and text
    verdictBadge.className = result.prediction === 'FAKE'
        ? 'verdict-fake badge-red'
        : 'verdict-real badge-green';
    verdictBadge.textContent = result.prediction;

    // Animate confidence bar
    confidenceBar.style.width = (result.confidence * 100) + '%';
    confidenceText.textContent = Math.round(result.confidence * 100) + '%';

    // Render keywords as chips
    keywordsContainer.innerHTML = result.keywords
        .map(k => `<span class="keyword-chip">${k}</span>`)
        .join('');

    // Render suspicious phrases
    suspiciousContainer.innerHTML = result.suspicious_phrases
        .map(p => `<span class="suspicious-chip">${p}</span>`)
        .join('');

    // Show/hide fact checks section
    if (result.fact_checks?.length > 0) {
        renderFactChecks(result.fact_checks);
    }
}
```

---

## Static Asset Serving

Flask serves static files automatically from the `static/` directory:

```python
# In templates, reference static files:
# {{ url_for('static', filename='css/style.css') }}
# {{ url_for('static', filename='js/dashboard.js') }}
```

URL pattern: `http://localhost:5000/static/<path>`
