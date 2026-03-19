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


_migrate_add_story_ender()
_migrate_add_equipped_slots()
_migrate_add_equipped_image_url()

app = FastAPI(title="Questly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.get("/")
def root():
    return {"message": "Questly API", "docs": "/docs"}


@app.on_event("startup")
def startup():
    from seed import seed_defaults
    seed_defaults()
