# Questly - Gamified To-Do List App

## Project Overview
A gamified to-do list app for a DH301 AI class project. Tasks are "quests" that earn XP, coins, and gems. Single-user mode (no auth). Google Calendar integration for syncing events as quests. Gmail inbox monitoring uses Gemini AI to parse actionable emails into scheduled tasks. An AI-powered narrative system (backed by Google Gemini or Anthropic Claude) can turn completed quests into story segments, building an ongoing storyline over time.

## Tech Stack
- **Frontend:** React 18 + Vite + React Router + CSS Modules
- **Backend:** Python FastAPI + SQLAlchemy + SQLite
- **Database:** SQLite (`backend/questly.db`, auto-created on first run)
- **Google Calendar:** OAuth 2.0 + Google Calendar API for event sync
- **Styling:** OSRS-inspired dark theme with genre-based color theming (CSS `--accent-rgb` variable + `[data-theme]` selectors). Cinzel + Outfit fonts

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
│   ├── story_generator.py   # AI story generation (Gemini/Claude) with personal context injection
│   ├── requirements.txt
│   ├── .env                 # Google OAuth + Anthropic secrets (gitignored)
│   ├── .env.example         # Template for required env vars (incl. ANTHROPIC_API_KEY)
│   └── routers/
│       ├── tasks.py         # Task CRUD + /complete with reward + recurrence cloning + story gen
│       ├── profile.py       # Get/update single-user profile (incl. genre, interests, life_variables, story_elements)
│       ├── shop.py          # Shop items + purchase with coins/gems
│       ├── gcal.py          # Google Calendar OAuth (PKCE disabled) + sync + keyword management
│       ├── gmail.py         # Gmail inbox monitoring + Gemini AI email parsing
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
        │   ├── Profile.jsx    # Stats, XP bar, interests, story characters, story elements, settings
        │   ├── Onboarding.jsx # Multi-step character creation (name, genre, interests, characters, story elements)
        │   └── Onboarding.module.css
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
# AI story: use ONE. Gemini = free at https://aistudio.google.com/apikey (no card). Anthropic = paid/credits.
GEMINI_API_KEY=<your-gemini-api-key>
# ANTHROPIC_API_KEY=<your-anthropic-api-key>
```

## Key Architecture Decisions
- **Single-user:** Profile table always has id=1, no auth needed. Add `user_id` FK later if needed.
- **Genre preference** stored on profile and fed into the AI story generator to control narrative tone.
- **Reward scaling:** Easy (10xp/5c), Medium (25xp/15c/1g), Hard (50xp/30c/3g), Extreme (100xp/60c/5g).
- **Level-up:** XP threshold = 100 * current_level.
- **Separate routers** for tasks, profile, shop, gcal, story — keeps AI narrative endpoints isolated and easy to evolve.
- **Task recurrence:** Clone-on-complete. Completing a daily/weekly task creates a new pending copy with the next due_date. The completed task stays as history.
- **Google Calendar sync:** OAuth 2.0 flow → fetches 30 days of events → creates Task records with auto-difficulty based on keywords. Tasks track `source="gcal"` and `source_id` for deduplication.
- **Gmail inbox monitoring:** Uses the same Google OAuth token (with `gmail.readonly` scope). On "Sync Inbox", fetches last 7 days of emails, sends batch to Gemini AI to identify actionable emails, and creates tasks with AI-extracted titles, due dates, and difficulty. Non-actionable emails (newsletters, receipts, notifications) are skipped. Tasks track `source="gmail"` and `source_id=message_id` for deduplication.
- **AI story generation (backend):** Story segments are generated via **Google Gemini** or **Anthropic Claude** when the corresponding API key is set; stored in `StorySegment` and exposed by the story router. Each segment uses the completed quest as a plot event and ends on a cliffhanger unless the task is marked **Story ender**, in which case the AI writes a conclusion. If no key is set or the call fails, completions and rewards still succeed; story generation is skipped.
- **Personal context in stories:** The story generator's `_build_personal_context(profile)` helper extracts likes/dislikes from `profile.interests` (JSON), character entries from `profile.life_variables` (JSON array), and free-form directions from `profile.story_elements` (text). This block is appended to every system prompt with instructions to weave details naturally without forcing every detail into every paragraph.
- **Onboarding gate:** `profile.setup_complete` (boolean, default false) controls whether the app shows the onboarding flow or the normal dashboard. When false, `App.jsx` renders only `<Onboarding>` (no Navbar, no routes). Completing onboarding sets `setup_complete: true` and the normal app loads.
- **Genre-based color theming:** CSS uses `--accent-rgb` variable pattern allowing `rgba(var(--accent-rgb), opacity)` throughout all module CSS files. `[data-theme]` attribute selectors on `<html>` override the RGB values per genre: fantasy (gold, default), sci-fi (neon green), mystery (noir/silver), horror (dark purple), adventure (light blue), comedy (warm red). App.jsx sets the attribute based on `profile.genre_preference`.
- **OAuth PKCE disabled:** Google OAuth flow has PKCE explicitly disabled (`flow.autogenerate_code_verifier = False`) because the stateless callback can't persist the code_verifier between auth URL generation and token exchange.

## API Endpoints
- `GET/POST /api/tasks` — List/create tasks
- `GET/PUT/DELETE /api/tasks/{id}` — Single task CRUD
- `POST /api/tasks/{id}/complete` — Mark complete + award rewards + clone if recurring
- `GET/PUT /api/profile` — Get/update profile (PUT accepts `equipped_hat/face/body/hand: int|null` to equip/unequip)
- `GET /api/shop` — List shop items
- `POST /api/shop/buy/{item_id}?currency=coins|gems` — Purchase item
- `POST /api/shop/equip/{item_id}` — Equip a purchased accessory (sets the matching slot on profile)
- `GET /api/shop/purchases` — List purchases
- `GET /images/{filename}` — Static file serving for avatar images
- `GET /api/gcal/status` — Google Calendar connection status
- `GET /api/gcal/auth-url` — Get OAuth authorization URL
- `GET /api/gcal/callback` — OAuth callback handler
- `POST /api/gcal/sync` — Sync events from Google Calendar
- `POST /api/gcal/disconnect` — Disconnect Google Calendar
- `GET/PUT /api/gcal/keywords` — Manage difficulty classification keywords
- `GET /api/story` — Get the full narrative as a list of story segments (oldest first)
- `POST /api/story/reset` — Delete all story segments and start a fresh narrative on the next completion
- `GET /api/gmail/status` — Check if Gmail scope is granted
- `POST /api/gmail/sync` — Fetch recent emails, parse actionable ones with Gemini AI, create tasks

## Avatar System
- **Images** live in `DH301/images/` and are served as static files at `/images/` by FastAPI
- **Base avatar**: `avatar_base.png` — always displayed, no purchase required
- **Accessories** are organized into four equippable slots: `hat`, `face`, `body`, `hand`
- **Layering**: images are transparent PNGs drawn to the same canvas size; stacked with `position: absolute` so they overlay the base avatar perfectly
- **Equip flow**: buy item in Shop → "Equip" button appears → `POST /api/shop/equip/{id}` sets `profile.equipped_{slot}` → Profile page re-renders with new layer
- **Unequip**: click "Remove" in Shop card → `PUT /api/profile` with `{equipped_hat: null}` etc.
- **One item per slot**: equipping a new hat auto-replaces the old one

## Database Models (notable fields)
### Profile
- `google_token` — serialized OAuth credentials
- `google_calendar_id` — which calendar to sync (default: "primary")
- `difficulty_keywords` — JSON string of custom difficulty keywords
- `equipped_hat/face/body/hand` — ShopItem.id of currently equipped accessory in each slot (nullable int)
- `setup_complete` — boolean, gates onboarding vs normal app (default false)
- `interests` — JSON string `{"likes": [...], "dislikes": [...]}`, fed into AI story prompts
- `life_variables` — JSON array `[{"name": "Mark", "role": "antagonist", "description": "Mark from accounting"}]`, woven into stories as characters
- `story_elements` — free-form text with extra story directions (settings, plotlines, etc.), appended to AI system prompts

### Task
- `recurrence` — "none", "daily", or "weekly"
- `source` — "gcal" or null (manual)
- `source_id` — Google Calendar event ID (for deduplication)
- `story_ender` — if true, completing this task prompts the AI to conclude the current story arc instead of adding a cliffhanger

### StorySegment
- `task_id` — FK to the task that generated this segment
- `content` — 2–3 sentence story text (from Gemini or Claude)
- `genre` — snapshot of the profile’s `genre_preference` when the segment was created
- `created_at` — when the segment was written

## Common Issues
- **Port 8000 in use:** Run `powershell "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force"` to free it.
- **Database reset:** Delete `backend/questly.db` and restart the backend — it will recreate and re-seed automatically.
- **Google Calendar issues:** Ensure `.env` file exists in `backend/` with valid credentials. Delete DB and restart if token gets corrupted.
 - **AI story issues:** Set either `GEMINI_API_KEY` (free at [Google AI Studio](https://aistudio.google.com/apikey)) or `ANTHROPIC_API_KEY`. If both are missing or invalid, task completion and rewards still work; the story field will be `null`. After adding new tables or columns (e.g. StorySegment, Task.story_ender), delete `backend/questly.db` and restart the backend to recreate the schema.
 - **New shop items not showing:** The seed only runs if the shop table is empty. To get real accessory items after upgrading from placeholder items, delete `backend/questly.db` and restart the backend.
 - **Avatar images not loading:** Ensure the backend is running (images are served from `/images/` by FastAPI). The Vite proxy forwards `/images` to the backend.


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
