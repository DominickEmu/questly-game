from __future__ import annotations

import json
import traceback
from datetime import date, timedelta

from config import GEMINI_API_KEY

SYSTEM_PROMPT = """You analyze emails and determine if they contain actionable tasks that require the recipient to DO something specific.

Return null for emails that are NOT actionable:
- Newsletters, marketing, promotions
- Order confirmations, shipping notifications, receipts
- Social media notifications
- Automated alerts with no required action
- FYI/informational emails with nothing to do

Return a task object for emails that ARE actionable — the recipient needs to complete something:
- Assignments, project requests, deadlines
- Meeting prep or follow-up action items
- Requests from people asking the user to do something
- Emails with explicit deadlines or due dates

Today's date is {today} ({weekday}).
Resolve relative dates: "Friday" = {friday}, "next week" = {next_monday}, "end of month" = {eom}.

Return ONLY a JSON array with one entry per email. Each entry is either null or:
{{"title": "short task title", "description": "brief context from the email", "due_date": "YYYY-MM-DD or null", "difficulty": "easy|medium|hard|extreme"}}

Difficulty guide:
- easy: simple/quick tasks (reply to email, read something, small updates)
- medium: moderate effort (write a document section, review something, attend meeting)
- hard: significant effort (complete a project, prepare a presentation, write a report)
- extreme: major undertaking (thesis, multi-day project, exam prep)

Return ONLY the JSON array, no other text."""


def _get_date_context() -> dict:
    today = date.today()
    weekday = today.strftime("%A")
    # Find next Friday
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    friday = today + timedelta(days=days_until_friday)
    # Next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    # End of month
    if today.month == 12:
        eom = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        eom = date(today.year, today.month + 1, 1) - timedelta(days=1)

    return {
        "today": today.isoformat(),
        "weekday": weekday,
        "friday": friday.isoformat(),
        "next_monday": next_monday.isoformat(),
        "eom": eom.isoformat(),
    }


def parse_emails(emails: list[dict]) -> list[dict | None]:
    """Parse a batch of emails using Gemini. Returns a list of task dicts or None per email.

    Each email dict should have: subject, snippet, date.
    Returns empty list on failure.
    """
    if not emails:
        return []
    if not GEMINI_API_KEY:
        return [None] * len(emails)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        date_ctx = _get_date_context()
        system = SYSTEM_PROMPT.format(**date_ctx)

        lines = []
        for i, email in enumerate(emails, 1):
            lines.append(
                f'{i}. Subject: "{email["subject"]}" | '
                f'Snippet: "{email["snippet"]}" | '
                f'Date: {email["date"]}'
            )
        user_msg = "Emails to analyze:\n" + "\n".join(lines)

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=1200,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )

        if not response or not response.text:
            return [None] * len(emails)

        # Extract JSON from response (strip markdown fences if present)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        results = json.loads(text)
        if not isinstance(results, list):
            return [None] * len(emails)

        # Pad or trim to match input length
        while len(results) < len(emails):
            results.append(None)
        return results[: len(emails)]

    except Exception:
        traceback.print_exc()
        return [None] * len(emails)
