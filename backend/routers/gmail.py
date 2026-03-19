from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_SCOPES
from database import get_db
from models import Profile, Task

router = APIRouter(prefix="/gmail", tags=["gmail"])

_GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def _get_or_create_profile(db: Session) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        profile = Profile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _credentials_from_token(token_json: str):
    from google.oauth2.credentials import Credentials

    info = json.loads(token_json)
    return Credentials(
        token=info["token"],
        refresh_token=info.get("refresh_token"),
        token_uri=info.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )


def _serialize_credentials(creds) -> str:
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


def _has_gmail_scope(profile: Profile) -> bool:
    if not profile.google_token:
        return False
    try:
        info = json.loads(profile.google_token)
        scopes = info.get("scopes") or []
        return any("gmail" in s for s in scopes)
    except Exception:
        return False


# ── Status ───────────────────────────────────────────────


@router.get("/status")
def gmail_status(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    return {"connected": _has_gmail_scope(profile)}


# ── Sync ─────────────────────────────────────────────────


@router.post("/sync")
def gmail_sync(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    if not profile.google_token:
        raise HTTPException(400, "Google account is not connected. Connect via Google Calendar first.")
    if not _has_gmail_scope(profile):
        raise HTTPException(
            400,
            "Gmail access not granted. Disconnect and reconnect Google to grant inbox permissions.",
        )

    creds = _credentials_from_token(profile.google_token)

    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request

        creds.refresh(Request())
        profile.google_token = _serialize_credentials(creds)
        db.commit()

    service = build("gmail", "v1", credentials=creds)

    # Fetch messages from last 7 days
    results = (
        service.users()
        .messages()
        .list(userId="me", q="newer_than:7d", maxResults=50)
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return {"imported": 0, "skipped": 0}

    # Load existing gmail source IDs for deduplication
    existing_source_ids: set[str] = {
        sid
        for (sid,) in db.query(Task.source_id).filter(Task.source == "gmail").all()
        if sid
    }

    # Fetch message details for new messages only
    new_emails = []
    new_message_ids = []
    for msg in messages:
        msg_id = msg["id"]
        if msg_id in existing_source_ids:
            continue

        detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["Subject", "Date"])
            .execute()
        )

        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(No subject)")
        snippet = detail.get("snippet", "")
        email_date = headers.get("Date", "")

        new_emails.append({"subject": subject, "snippet": snippet, "date": email_date})
        new_message_ids.append(msg_id)

        # Limit batch size to avoid overwhelming the AI
        if len(new_emails) >= 15:
            break

    if not new_emails:
        return {"imported": 0, "skipped": len(messages)}

    # Parse emails with AI
    from gmail_parser import parse_emails

    parsed = parse_emails(new_emails)

    imported = 0
    skipped = len(messages) - len(new_emails)

    for i, result in enumerate(parsed):
        if result is None:
            skipped += 1
            continue

        try:
            due_date = None
            if result.get("due_date"):
                due_date = date.fromisoformat(result["due_date"])

            difficulty = result.get("difficulty", "medium")
            if difficulty not in ("easy", "medium", "hard", "extreme"):
                difficulty = "medium"

            task = Task(
                title=result.get("title", new_emails[i]["subject"])[:200],
                description=result.get("description", "")[:500],
                difficulty=difficulty,
                due_date=due_date,
                recurrence="none",
                source="gmail",
                source_id=new_message_ids[i],
            )
            db.add(task)
            imported += 1
        except Exception:
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped}
