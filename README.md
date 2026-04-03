# Shaw P4 Action Tracker

A secure, web-based action item tracker for Shaw Flooring Plant 4 Coating Process Engineering. Track daily action items organized by strategic objectives, collaborate with comments and suggestions, and build a knowledge base with built-in wiki pages.

Built with Flask, PostgreSQL, and an Apple glassmorphism UI (black and purple theme).

---

## Features

### Action Item Tracking
- **10 Strategic Objectives** pre-loaded (Latex ATS, FPM ATS, Reduce MSM, Reduce Stops, Loose Edges, Off-Quality Reduction, Waste/Industrial, Ignition Dashboards, Other Tier, Stretch)
- Create **Projects** under each objective (e.g., "Reduce Stops" → "Pretenter EIT")
- Track **Action Items** with title, description, source, priority (low/medium/high/critical), status, due date, and notes
- Click-to-cycle status toggle (Open → In Progress → Completed) via AJAX
- Dashboard with progress bars and counts per objective

### Collaboration
- **Comments, Suggestions, and Questions** on any objective, project, or action item
- **Activity Feed** showing recent comments and updated items across all objectives
- Each comment displays author, type badge, and timestamp

### Wiki
- Create reference pages for definitions, procedures, and documentation
- Use `[[Page Name]]` syntax anywhere (descriptions, notes, comments) to auto-link to wiki pages
- Clicking a link to a page that doesn't exist yet offers to create it

### Security
- Bcrypt password hashing (no plaintext passwords)
- CSRF tokens on every form (Flask-WTF)
- SQLAlchemy ORM for all queries (no raw SQL, no SQL injection)
- `@login_required` on all tracker routes
- All secrets loaded from environment variables
- No API keys in source code

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.11, Flask 3.0              |
| Database   | PostgreSQL (Railway) / SQLite (local) |
| Auth       | Flask-Login + Flask-Bcrypt          |
| Forms      | Flask-WTF with CSRF protection      |
| ORM        | Flask-SQLAlchemy                    |
| Frontend   | Jinja2, CSS3 glassmorphism, vanilla JS |
| Deployment | Railway + Gunicorn                  |

---

## Setup

### Prerequisites

- Python 3.11+
- pip
- Git
- (Optional) A Railway account for deployment

### 1. Clone the repository

```bash
git clone https://github.com/netprocesssolutions/jordantaylor.git
cd jordantaylor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file in the project root (this file is gitignored):

```
SECRET_KEY=your-random-secret-key-here
ADMIN_PASSWORD=your-desired-password
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Seed the database

This creates the SQLite database, the admin user, and all 10 strategic objectives:

```bash
python seed.py
```

You should see:

```
Created admin user: jordan (password: <your password>)
Created objective: 1. Latex ATS
Created objective: 2. FPM ATS
...
Seed complete!
```

### 5. Run the app

```bash
python app.py
```

The app starts at `http://localhost:5000`.

- **Portfolio:** `http://localhost:5000/`
- **Tracker login:** `http://localhost:5000/tracker/login`
- **Username:** `jordan`
- **Password:** whatever you set in `ADMIN_PASSWORD` (default: `changeme123`)

---

## Deploy to Railway

### 1. Create a new project on Railway

Connect your GitHub repository to Railway.

### 2. Add a PostgreSQL plugin

In your Railway project dashboard, click **+ New** → **Database** → **PostgreSQL**. This automatically sets the `DATABASE_URL` environment variable.

### 3. Set environment variables

In your Railway service settings, add:

| Variable         | Value                                      |
|------------------|--------------------------------------------|
| `SECRET_KEY`     | A long random string (use the command above) |
| `ADMIN_PASSWORD` | Your desired login password                 |

`DATABASE_URL` is set automatically by the PostgreSQL plugin.

### 4. Deploy

Push to your branch or trigger a deploy from the Railway dashboard. The `Procfile` runs the seed script automatically before starting the server:

```
web: python seed.py && gunicorn app:app --bind 0.0.0.0:$PORT
```

### 5. Configure custom domain (optional)

In Railway service settings → **Networking** → **Custom Domain**, add your domain (e.g., `jordantaylor.online`) and update your DNS records as instructed.

---

## Project Structure

```
jordantaylor/
├── app.py                    # Flask app factory + portfolio routes
├── models.py                 # SQLAlchemy models (User, Objective, Project, ActionItem, Comment, WikiPage)
├── tracker.py                # Tracker blueprint (all tracker routes)
├── forms.py                  # Flask-WTF form classes
├── seed.py                   # Database seed script (admin user + objectives)
├── requirements.txt          # Python dependencies
├── Procfile                  # Railway/Gunicorn startup command
├── runtime.txt               # Python version for Railway
├── .gitignore
├── static/
│   ├── css/
│   │   ├── style.css         # Portfolio styles
│   │   └── tracker.css       # Tracker glassmorphism theme (black/purple)
│   └── js/
│       ├── main.js           # Portfolio JavaScript
│       └── tracker.js        # Tracker interactivity (AJAX status toggle, flash fade)
└── templates/
    ├── base.html             # Portfolio base template
    ├── index.html            # Portfolio home
    ├── resume.html           # Portfolio resume
    ├── projects.html         # Portfolio projects
    ├── contact.html          # Portfolio contact
    ├── 404.html              # Error page
    └── tracker/
        ├── base_tracker.html       # Tracker base layout
        ├── login.html              # Login page
        ├── dashboard.html          # Objectives overview
        ├── objective_detail.html   # Single objective with projects + items
        ├── action_item_form.html   # Create/edit action item
        ├── project_form.html       # Create/edit project
        ├── feed.html               # Activity feed
        ├── wiki_index.html         # Wiki page listing
        ├── wiki_page.html          # Single wiki page
        └── wiki_form.html          # Create/edit wiki page
```

---

## Usage

### Daily Workflow

1. **Log in** at `/tracker/login`
2. **Dashboard** shows all 10 strategic objectives with progress
3. **Click an objective** to see its projects and action items
4. **Add action items** as they come in from meetings, emails, floor walks
5. **Toggle status** by clicking the circle icon (Open → In Progress → Completed)
6. **Add comments** on items to log updates, suggestions, or questions
7. **Check the feed** at `/tracker/feed` for recent activity
8. **Build the wiki** with definitions and procedures — link from anywhere with `[[Page Name]]`

### Wiki Linking

Type `[[SBR Latex]]` in any text field (description, notes, comments) and it becomes a clickable link to a wiki page called "SBR Latex". If the page doesn't exist yet, clicking it will offer to create it.
