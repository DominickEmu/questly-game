import os

# Allow OAuth over HTTP for local development
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from database import Base, engine
from routers import tasks, profile, shop, gcal, story, gmail

Base.metadata.create_all(bind=engine)


def _migrate_add_story_ender():
    """Add story_ender column to tasks if it doesn't exist (for existing DBs)."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(tasks)"))
        columns = [row[1] for row in result]
        if "story_ender" not in columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN story_ender BOOLEAN DEFAULT 0"))
            conn.commit()


def _migrate_add_equipped_slots():
    """Add equipped_* columns to profile if they don't exist (for existing DBs)."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(profile)"))
        columns = [row[1] for row in result]
        for col in ("equipped_hat", "equipped_face", "equipped_body", "equipped_hand"):
            if col not in columns:
                conn.execute(text(f"ALTER TABLE profile ADD COLUMN {col} INTEGER"))
        conn.commit()


def _migrate_add_equipped_image_url():
    """Add equipped_image_url column to shop_items if it doesn't exist."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(shop_items)"))
        columns = [row[1] for row in result]
        if "equipped_image_url" not in columns:
            conn.execute(text("ALTER TABLE shop_items ADD COLUMN equipped_image_url TEXT"))
            conn.commit()


def _migrate_add_onboarding_fields():
    """Add setup_complete, interests, life_variables to profile if missing."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(profile)"))
        columns = [row[1] for row in result]
        if "setup_complete" not in columns:
            conn.execute(text("ALTER TABLE profile ADD COLUMN setup_complete BOOLEAN DEFAULT 0"))
            conn.execute(text("UPDATE profile SET setup_complete = 1 WHERE username != 'Adventurer'"))
        if "interests" not in columns:
            conn.execute(text("ALTER TABLE profile ADD COLUMN interests TEXT"))
        if "life_variables" not in columns:
            conn.execute(text("ALTER TABLE profile ADD COLUMN life_variables TEXT"))
        if "story_elements" not in columns:
            conn.execute(text("ALTER TABLE profile ADD COLUMN story_elements TEXT"))
        conn.commit()


def _migrate_add_story_archives():
    """Create story_archives table if it doesn't exist (for existing DBs)."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='story_archives'"))
        if not result.fetchone():
            conn.execute(text("""
                CREATE TABLE story_archives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    segments_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()


def _migrate_add_segment_rating():
    """Add rating and feedback columns to story_segments if missing."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(story_segments)"))
        columns = [row[1] for row in result]
        if "rating" not in columns:
            conn.execute(text("ALTER TABLE story_segments ADD COLUMN rating INTEGER DEFAULT 0"))
        if "feedback" not in columns:
            conn.execute(text("ALTER TABLE story_segments ADD COLUMN feedback TEXT"))
        conn.commit()


_migrate_add_story_ender()
_migrate_add_equipped_slots()
_migrate_add_equipped_image_url()
_migrate_add_onboarding_fields()
_migrate_add_story_archives()
_migrate_add_segment_rating()

app = FastAPI(title="Questly API")

from config import FRONTEND_ORIGIN
_allowed_origins = list({o for o in [
    "http://localhost:5173",
    "http://localhost:8000",
    FRONTEND_ORIGIN,
] if o})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(shop.router, prefix="/api")
app.include_router(gcal.router, prefix="/api")
app.include_router(story.router, prefix="/api")
app.include_router(gmail.router, prefix="/api")

_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
app.mount("/images", StaticFiles(directory=_images_dir), name="images")

# Serve the React SPA when built frontend is present (production / Docker)
_frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
if os.path.exists(_frontend_dist):
    _assets_dir = os.path.join(_frontend_dist, "assets")
    if os.path.exists(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        from fastapi.responses import FileResponse
        candidate = os.path.join(_frontend_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_frontend_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "Questly API — run the frontend separately in dev", "docs": "/docs"}


@app.on_event("startup")
def startup():
    from seed import seed_defaults
    seed_defaults()
