from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from config import (
    FRONTEND_ORIGIN,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
)
from database import get_db
from models import Profile, Task

router = APIRouter(prefix="/gcal", tags=["google-calendar"])


def _get_or_create_profile(db: Session) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        profile = Profile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _build_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(
        client_config, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI
    )
    return flow


def _credentials_from_token(token_json: str) -> Credentials:
    info = json.loads(token_json)
    return Credentials(
        token=info["token"],
        refresh_token=info.get("refresh_token"),
        token_uri=info.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )


def _serialize_credentials(creds: Credentials) -> str:
    return json.dumps(
        {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
    )


# ── Status ───────────────────────────────────────────────


@router.get("/status")
def gcal_status(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    connected = profile.google_token is not None
    return {
        "connected": connected,
        "calendar_id": profile.google_calendar_id or "primary",
    }


# ── Auth URL ─────────────────────────────────────────────


@router.get("/auth-url")
def gcal_auth_url():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            500, "Google OAuth credentials not configured on the server."
        )

    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"url": auth_url}


# ── OAuth Callback ───────────────────────────────────────


@router.get("/callback")
def gcal_callback(code: str = Query(...), db: Session = Depends(get_db)):
    flow = _build_flow()
    flow.fetch_token(code=code)

    creds = flow.credentials
    profile = _get_or_create_profile(db)
    profile.google_token = _serialize_credentials(creds)
    db.commit()

    return RedirectResponse(f"{FRONTEND_ORIGIN}/profile?gcal=connected")


# ── Sync ─────────────────────────────────────────────────


def _parse_event_date(event: dict) -> date | None:
    """Extract a Python date from a Google Calendar event start."""
    start = event.get("start", {})
    if "date" in start:
        return date.fromisoformat(start["date"])
    if "dateTime" in start:
        return datetime.fromisoformat(start["dateTime"]).date()
    return None


def _event_duration_minutes(event: dict) -> float | None:
    """Return event duration in minutes, or None for all-day events."""
    start = event.get("start", {})
    end = event.get("end", {})
    if "dateTime" in start and "dateTime" in end:
        s = datetime.fromisoformat(start["dateTime"])
        e = datetime.fromisoformat(end["dateTime"])
        return (e - s).total_seconds() / 60
    return None


_DEFAULT_HARD_KEYWORDS = [
    "exam", "final", "midterm", "test", "quiz", "defense", "defence",
    "presentation", "deadline", "submission", "demo", "interview",
    "assessment", "evaluation", "thesis", "dissertation", "proposal",
]
_DEFAULT_EASY_KEYWORDS = [
    "lunch", "break", "coffee", "snack", "walk", "stretch",
    "check-in", "checkin", "standup", "stand-up", "sync",
    "1:1", "one-on-one", "casual", "social", "hangout", "chat",
]


def _load_keyword_lists(profile: Profile) -> tuple[set[str], set[str]]:
    """Return (hard_keywords, easy_keywords) merging defaults with user custom ones,
    minus any defaults the user explicitly removed."""
    hard = set(_DEFAULT_HARD_KEYWORDS)
    easy = set(_DEFAULT_EASY_KEYWORDS)

    if profile.difficulty_keywords:
        custom = json.loads(profile.difficulty_keywords)
        hard.update(kw.lower().strip() for kw in custom.get("hard", []) if kw.strip())
        easy.update(kw.lower().strip() for kw in custom.get("easy", []) if kw.strip())

        for kw in custom.get("removed_hard", []):
            hard.discard(kw.lower().strip())
        for kw in custom.get("removed_easy", []):
            easy.discard(kw.lower().strip())

    return hard, easy


def _classify_difficulty(
    event: dict,
    hard_keywords: set[str],
    easy_keywords: set[str],
) -> str:
    text = (event.get("summary", "") + " " + (event.get("description") or "")).lower()

    for kw in hard_keywords:
        if kw in text:
            return "hard"
    for kw in easy_keywords:
        if kw in text:
            return "medium"

    return "easy"


@router.post("/sync")
def gcal_sync(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    if not profile.google_token:
        raise HTTPException(400, "Google Calendar is not connected.")

    creds = _credentials_from_token(profile.google_token)

    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request

        creds.refresh(Request())
        profile.google_token = _serialize_credentials(creds)
        db.commit()

    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=30)).isoformat()

    calendar_id = profile.google_calendar_id or "primary"
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=250,
        )
        .execute()
    )

    events = events_result.get("items", [])

    existing_source_ids: set[str] = {
        sid
        for (sid,) in db.query(Task.source_id).filter(Task.source == "gcal").all()
        if sid
    }

    hard_kw, easy_kw = _load_keyword_lists(profile)

    imported = 0
    skipped = 0

    for event in events:
        event_id = event["id"]
        if event_id in existing_source_ids:
            skipped += 1
            continue

        summary = event.get("summary", "(No title)")
        description = event.get("description")
        due = _parse_event_date(event)
        difficulty = _classify_difficulty(event, hard_kw, easy_kw)

        task = Task(
            title=summary,
            description=description,
            difficulty=difficulty,
            due_date=due,
            recurrence="none",
            source="gcal",
            source_id=event_id,
        )
        db.add(task)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped}


# ── Keywords ─────────────────────────────────────────────


@router.get("/keywords")
def get_keywords(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    custom = {"hard": [], "easy": [], "removed_hard": [], "removed_easy": []}
    if profile.difficulty_keywords:
        saved = json.loads(profile.difficulty_keywords)
        custom.update(saved)
    return {
        "defaults": {
            "hard": _DEFAULT_HARD_KEYWORDS,
            "easy": _DEFAULT_EASY_KEYWORDS,
        },
        "custom": custom,
    }


@router.put("/keywords")
def update_keywords(body: dict, db: Session = Depends(get_db)):
    hard = [kw.strip().lower() for kw in body.get("hard", []) if kw.strip()]
    easy = [kw.strip().lower() for kw in body.get("easy", []) if kw.strip()]
    removed_hard = [kw.strip().lower() for kw in body.get("removed_hard", []) if kw.strip()]
    removed_easy = [kw.strip().lower() for kw in body.get("removed_easy", []) if kw.strip()]
    profile = _get_or_create_profile(db)
    profile.difficulty_keywords = json.dumps({
        "hard": hard,
        "easy": easy,
        "removed_hard": removed_hard,
        "removed_easy": removed_easy,
    })
    db.commit()
    return {"hard": hard, "easy": easy, "removed_hard": removed_hard, "removed_easy": removed_easy}


# ── Disconnect ───────────────────────────────────────────


@router.delete("/disconnect", status_code=204)
def gcal_disconnect(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    profile.google_token = None
    db.commit()
