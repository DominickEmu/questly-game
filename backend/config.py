import os
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent / ".env"

if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/gcal/callback"
)
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.events.readonly"]

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
