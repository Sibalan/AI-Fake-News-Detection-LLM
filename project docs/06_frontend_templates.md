# Module 06 — Frontend Templates

## Files
- `templates/base.html` — Base layout
- `templates/index.html` — Landing page
- `templates/login.html` — Login form
- `templates/signup.html` — Registration form
- `templates/dashboard.html` — User dashboard
- `templates/detect.html` — News analysis page
- `templates/history.html` — Prediction history
- `templates/about.html` — About page
- `templates/contact.html` — Contact form
- `templates/change_password.html` — Password change
- `templates/admin_panel.html` — Admin interface
- `templates/admin/dashboard.html` — Admin analytics
- `templates/components/navbar.html` — Navigation bar
- `templates/components/footer.html` — Footer

---

## Template Engine

Templates use **Jinja2** (Flask's default) with **Tailwind CSS** for styling.

```html
<!-- Jinja2 template inheritance -->
{% extends "base.html" %}
{% block content %}
  <!-- page content here -->
{% endblock %}
```

---

## `base.html` — Base Layout

Defines the shared HTML structure inherited by all other pages.

**Provides**:
- `<head>` with Tailwind CDN, custom CSS, and meta tags
- `{% include "components/navbar.html" %}` navigation
- `{% block content %}` placeholder for page content
- `{% include "components/footer.html" %}` footer
- Global JavaScript (auth check, token management)

**Template Blocks**:
| Block | Purpose |
|---|---|
| `{% block title %}` | Page `<title>` tag |
| `{% block head %}` | Extra `<head>` content |
| `{% block content %}` | Main page body |
| `{% block scripts %}` | Page-specific scripts |

---

## `components/navbar.html` — Navigation Bar

Responsive navigation component with:
- Brand logo/name
- Navigation links (Home, About, Contact)
- Auth-aware state: shows Login/Signup when logged out, Dashboard/Logout when logged in
- Admin link if user has admin role
- Mobile hamburger menu

Uses JavaScript to check `localStorage` for JWT token to toggle auth state.

---

## `components/footer.html` — Footer

Static footer with:
- Project name and brief description
- Navigation links
- Copyright notice

---

## `index.html` — Landing Page

Hero section introducing the fake news detector.

**Sections**:
1. **Hero** — Headline, subtext, CTA buttons ("Try Now", "Learn More")
2. **How It Works** — 3-step visual explanation (Input → AI Analysis → Result)
3. **Features** — Cards for Groq LLM, Fact-checking, Sentiment Analysis, History
4. **Stats** — Animated counters (articles analyzed, accuracy rate)

---

## `login.html` — Login Form

Simple centered card form.

**Fields**:
- Username or Email
- Password (with show/hide toggle)
- "Remember me" checkbox

**JavaScript**:
- Submits to `POST /api/auth/login`
- Stores JWT in `localStorage`
- Sets `session` via response
- Redirects to `/dashboard` on success
- Displays inline error messages on failure

---

## `signup.html` — Registration Form

**Fields**:
- Full Name (optional)
- Username (required)
- Email (required)
- Password (required)
- Confirm Password

**Client-side validation**:
- Password match check
- Minimum length feedback
- Real-time username availability check (debounced)

---

## `dashboard.html` — User Dashboard

Main user interface after login.

**Sections**:

### Stats Cards (top row)
| Card | Data Source |
|---|---|
| Total Analyses | `GET /api/history/stats` |
| Fake Detected | stats.fake_count |
| Real Detected | stats.real_count |
| Avg Confidence | stats.avg_confidence |

### News Analysis Form
- Large textarea for pasting article text
- Optional URL field
- "Analyze" button with loading spinner

### Result Display
Shows after analysis completes:
- REAL/FAKE badge with color coding (green/red)
- Confidence percentage bar
- Detection method badge (Groq/Ollama/Heuristic)
- Explanation text
- Sentiment badge
- Keywords chips
- Suspicious phrases list
- Fact-check results (if any)

### Recent History Table
- Last 5 predictions
- Columns: Date, Preview, Verdict, Confidence
- Link to full history page

---

## `detect.html` — Dedicated Analysis Page

Focused version of the analysis form (same as dashboard form section but full-page).

**Additional features**:
- Character count display
- Category detection display
- Processing time shown
- Share result button

---

## `history.html` — Prediction History

**Features**:
- Paginated table of all user predictions
- Filter tabs: All / REAL / FAKE
- Sort by date, confidence, method
- Search within history
- Delete individual records
- Clear all history button
- Each row expandable to show full explanation

**API calls**:
- `GET /api/history/?page=1&filter=all`
- `DELETE /api/history/<id>`
- `DELETE /api/history/clear`

---

## `admin_panel.html` — Admin Interface

Only accessible to admin users.

**Tabs**:
1. **Dashboard** — System stats, fake/real pie chart, method distribution chart
2. **Users** — Searchable, paginated user table with toggle active/inactive
3. **All Predictions** — System-wide prediction log with filters
4. **Timeline** — Line chart of daily prediction volumes

**Charts**: Uses Chart.js (loaded via CDN)

---

## `admin/dashboard.html` — Admin Analytics Dashboard

Dedicated admin analytics view with:
- Real-time counters refreshed on load
- Chart.js line chart for prediction trends
- Doughnut chart for REAL vs FAKE distribution
- Bar chart for detection methods

---

## `change_password.html` — Password Change

Simple form:
- Current password
- New password
- Confirm new password

Calls `POST /api/auth/change-password`.

---

## `about.html` — About Page

Static informational page describing:
- Project purpose
- Technology stack
- Team/course information (RVCE MCA Project)
- How the AI pipeline works

---

## `contact.html` — Contact Form

Form with name, email, subject, message fields. Client-side only (no backend endpoint — for display purposes).

---

## Jinja2 Template Variables

Pages receive these variables from Flask view functions:

| Variable | Type | Pages |
|---|---|---|
| `user` | dict or None | All pages with session |
| `error` | str or None | Login, signup |
| `success` | str or None | Change password |

---

## Authentication Flow in Templates

```javascript
// Check login state (in base.html script)
const token = localStorage.getItem('access_token');
if (!token && window.location.pathname === '/dashboard') {
    window.location.href = '/login';
}

// Logout
function logout() {
    localStorage.removeItem('access_token');
    fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/';
}
```
