# Questly - Gamified To-Do List App

## Project Overview
A gamified to-do list app for a DH301 AI class project. Tasks are "quests" that earn XP, coins, and gems. Single-user mode (no auth). AI story generation features planned for later.

## Tech Stack
- **Frontend:** React 18 + Vite + React Router + CSS Modules
- **Backend:** Python FastAPI + SQLAlchemy + SQLite
- **Database:** SQLite (`backend/questly.db`, auto-created on first run)

## Project Structure
```
DH301/
├── backend/
│   ├── main.py              # FastAPI entry point, CORS, router registration
│   ├── database.py          # SQLAlchemy engine + session (SQLite)
│   ├── models.py            # ORM models: Profile, Task, ShopItem, Purchase
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── seed.py              # Seeds default shop items + profile on startup
│   ├── requirements.txt
│   └── routers/
│       ├── tasks.py         # Task CRUD + /complete with reward logic
│       ├── profile.py       # Get/update single-user profile
│       └── shop.py          # Shop items + purchase with coins/gems
└── frontend/
    ├── vite.config.js       # Proxies /api to localhost:8000
    └── src/
        ├── main.jsx         # Entry point with BrowserRouter
        ├── App.jsx          # Routes + profile state
        ├── App.css          # Global styles (dark theme)
        ├── api.js           # Fetch wrapper for all backend calls
        ├── pages/
        │   ├── Dashboard.jsx  # Today's quests
        │   ├── Weekly.jsx     # Tasks grouped by weekday
        │   ├── Shop.jsx       # Buy items with currency
        │   └── Profile.jsx    # Stats, XP bar, settings
        └── components/
            ├── Navbar.jsx      # Nav links + currency display
            ├── TaskCard.jsx    # Single task with actions
            ├── TaskForm.jsx    # Add/edit task modal
            ├── RewardPopup.jsx # XP/coin popup on completion
            └── ShopItem.jsx    # Shop item card
```

## How to Run
```bash
# Terminal 1 - Backend (port 8000)
cd backend
python -m uvicorn main:app --reload

# Terminal 2 - Frontend (port 5173)
cd frontend
npm run dev
```
Open http://localhost:5173. Vite proxies `/api` requests to the backend.

## Key Architecture Decisions
- **Single-user:** Profile table always has id=1, no auth needed. Add `user_id` FK later if needed.
- **Genre preference** stored on profile now, ready for future AI story integration.
- **Reward scaling:** Easy (10xp/5c), Medium (25xp/15c/1g), Hard (50xp/30c/3g), Extreme (100xp/60c/5g).
- **Level-up:** XP threshold = 100 * current_level.
- **Separate routers** for tasks, profile, shop — easy to add an AI router later.

## API Endpoints
- `GET/POST /api/tasks` — List/create tasks
- `GET/PUT/DELETE /api/tasks/{id}` — Single task CRUD
- `POST /api/tasks/{id}/complete` — Mark complete + award rewards
- `GET/PUT /api/profile` — Get/update profile
- `GET /api/shop` — List shop items
- `POST /api/shop/buy/{item_id}?currency=coins|gems` — Purchase item
- `GET /api/shop/purchases` — List purchases

## Common Issues
- **Port 8000 in use:** Run `powershell "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force"` to free it.
- **Database reset:** Delete `backend/questly.db` and restart the backend — it will recreate and re-seed automatically.


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
