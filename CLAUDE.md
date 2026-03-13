# Questly - Gamified To-Do List App

## Project Overview
A gamified to-do list app for a DH301 AI class project. Tasks are "quests" that earn XP, coins, and gems. Single-user mode (no auth). Google Calendar integration for syncing events as quests. An AI-powered narrative system (backed by Anthropic Claude) can turn completed quests into story segments, building an ongoing storyline over time.

## Tech Stack
- **Frontend:** React 18 + Vite + React Router + CSS Modules
- **Backend:** Python FastAPI + SQLAlchemy + SQLite
- **Database:** SQLite (`backend/questly.db`, auto-created on first run)
- **Google Calendar:** OAuth 2.0 + Google Calendar API for event sync
- **Styling:** OSRS-inspired dark theme (dark browns, rustic golds, parchment tones) with Cinzel + Outfit fonts

## Project Structure
```
DH301/
├── backend/
│   ├── main.py              # FastAPI entry point, CORS, router registration
│   ├── config.py            # Environment config loader (Google OAuth + Anthropic creds)
│   ├── database.py          # SQLAlchemy engine + session (SQLite)
│   ├── models.py            # ORM models: Profile, Task, StorySegment, ShopItem, Purchase
│   ├── schemas.py           # Pydantic request/response schemas (incl. RewardOut.story, StorySegmentOut)
│   ├── seed.py              # Seeds default shop items + profile on startup
│   ├── story_generator.py   # Anthropic client + prompt templates + generate_story_segment()
│   ├── requirements.txt
│   ├── .env                 # Google OAuth + Anthropic secrets (gitignored)
│   ├── .env.example         # Template for required env vars (incl. ANTHROPIC_API_KEY)
│   └── routers/
│       ├── tasks.py         # Task CRUD + /complete with reward + recurrence cloning (prepared for story gen)
│       ├── profile.py       # Get/update single-user profile (incl. genre preference for story tone)
│       ├── shop.py          # Shop items + purchase with coins/gems
│       ├── gcal.py          # Google Calendar OAuth + sync + keyword management
│       └── story.py         # Story read/reset endpoints backed by StorySegment table
└── frontend/
    ├── vite.config.js       # Proxies /api to localhost:8000
    └── src/
        ├── main.jsx         # Entry point with BrowserRouter
        ├── App.jsx          # Routes + profile state
        ├── App.css          # Global styles (OSRS dark theme, CSS vars, animations)
        ├── api.js           # Fetch wrapper for all backend calls
        ├── pages/
        │   ├── Dashboard.jsx  # Today's quests (+ overdue pending)
        │   ├── Weekly.jsx     # Tasks grouped by weekday (current week only)
        │   ├── Calendar.jsx   # Full monthly calendar grid with day detail panel
        │   ├── Shop.jsx       # Buy items with currency
        │   └── Profile.jsx    # Stats, XP bar, settings
        └── components/
            ├── Navbar.jsx      # Nav links (5 pages) + currency display
            ├── TaskCard.jsx    # Single task with difficulty + recurrence badges
            ├── TaskForm.jsx    # Add/edit task modal
            ├── RewardPopup.jsx # XP/coin popup on completion + next quest notice (can show story snippet)
            └── ShopItem.jsx    # Shop item card
```

## How to Run
```bash
# Terminal 1 - Backend (port 8000)
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Terminal 2 - Frontend (port 5173)
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Vite proxies `/api` requests to the backend.

## Environment Variables
Create `backend/.env` with:
```
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/gcal/callback
FRONTEND_ORIGIN=http://localhost:5173
ANTHROPIC_API_KEY=<your-anthropic-api-key>  # from console.anthropic.com, used for AI story generation
```

## Key Architecture Decisions
- **Single-user:** Profile table always has id=1, no auth needed. Add `user_id` FK later if needed.
- **Genre preference** stored on profile and fed into the AI story generator to control narrative tone.
- **Reward scaling:** Easy (10xp/5c), Medium (25xp/15c/1g), Hard (50xp/30c/3g), Extreme (100xp/60c/5g).
- **Level-up:** XP threshold = 100 * current_level.
- **Separate routers** for tasks, profile, shop, gcal, story — keeps AI narrative endpoints isolated and easy to evolve.
- **Task recurrence:** Clone-on-complete. Completing a daily/weekly task creates a new pending copy with the next due_date. The completed task stays as history.
- **Google Calendar sync:** OAuth 2.0 flow → fetches 30 days of events → creates Task records with auto-difficulty based on keywords. Tasks track `source="gcal"` and `source_id` for deduplication.
- **AI story generation (backend):** Story segments are generated via Anthropic Claude when configured, stored in the `StorySegment` table, and can be read/reset via the story router. If the API key is missing or invalid, completions and rewards still succeed; story generation is skipped.

## API Endpoints
- `GET/POST /api/tasks` — List/create tasks
- `GET/PUT/DELETE /api/tasks/{id}` — Single task CRUD
- `POST /api/tasks/{id}/complete` — Mark complete + award rewards + clone if recurring
- `GET/PUT /api/profile` — Get/update profile
- `GET /api/shop` — List shop items
- `POST /api/shop/buy/{item_id}?currency=coins|gems` — Purchase item
- `GET /api/shop/purchases` — List purchases
- `GET /api/gcal/status` — Google Calendar connection status
- `GET /api/gcal/auth-url` — Get OAuth authorization URL
- `GET /api/gcal/callback` — OAuth callback handler
- `POST /api/gcal/sync` — Sync events from Google Calendar
- `POST /api/gcal/disconnect` — Disconnect Google Calendar
- `GET/PUT /api/gcal/keywords` — Manage difficulty classification keywords
 - `GET /api/story` — Get the full narrative as a list of story segments (oldest first)
 - `POST /api/story/reset` — Delete all story segments and start a fresh narrative on the next completion

## Database Models (notable fields)
### Profile
- `google_token` — serialized OAuth credentials
- `google_calendar_id` — which calendar to sync (default: "primary")
- `difficulty_keywords` — JSON string of custom difficulty keywords

### Task
- `recurrence` — "none", "daily", or "weekly"
- `source` — "gcal" or null (manual)
- `source_id` — Google Calendar event ID (for deduplication)

### StorySegment
- `task_id` — FK to the task that generated this segment
- `content` — 2–3 sentence story text generated by Claude
- `genre` — snapshot of the profile’s `genre_preference` when the segment was created
- `created_at` — when the segment was written

## Common Issues
- **Port 8000 in use:** Run `powershell "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force"` to free it.
- **Database reset:** Delete `backend/questly.db` and restart the backend — it will recreate and re-seed automatically.
- **Google Calendar issues:** Ensure `.env` file exists in `backend/` with valid credentials. Delete DB and restart if token gets corrupted.
 - **AI story issues:** If `ANTHROPIC_API_KEY` is missing or invalid, task completion and rewards still work; the story field will be `null` and no `StorySegment` will be written. After adding the StorySegment model, deleting `backend/questly.db` and restarting will recreate the DB with the new table.


DISTILLED_AESTHETICS_PROMPT = """
<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight. Focus on:

Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.

Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.

Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.

Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!
</frontend_aesthetics>
"""
