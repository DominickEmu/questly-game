from __future__ import annotations

import traceback
from sqlalchemy.orm import Session

from config import ANTHROPIC_API_KEY
from models import Task, Profile, StorySegment

_client = None


def _get_client():
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


GENRE_TONES = {
    "fantasy": "high fantasy with magic, swords, and ancient prophecies. Think medieval quests and enchanted forests.",
    "sci-fi": "science fiction with advanced technology, space exploration, and futuristic societies.",
    "mystery": "a detective mystery with clues, suspense, and unexpected twists lurking around every corner.",
    "horror": "dark horror with creeping dread, ominous shadows, and supernatural threats.",
    "adventure": "a swashbuckling adventure with daring escapades, treasure hunts, and narrow escapes.",
    "comedy": "a comedic romp with witty banter, absurd situations, and lighthearted chaos.",
}

CONTEXT_WINDOW = 5

SYSTEM_PROMPT = """You are a master storyteller narrating an ongoing {genre_tone}

RULES:
- Write EXACTLY 2-3 sentences continuing the story.
- The adventurer just completed a quest: use the quest details as a plot event in the narrative.
- Maintain continuity with any previous story segments provided.
- Write in second person ("You") to address the adventurer directly.
- Keep the tone consistent with the genre throughout.
- Do NOT use meta-commentary, do NOT break the fourth wall.
- Do NOT include quest titles or game mechanics in the narrative text.
- End the segment at a moment that creates anticipation for the next quest.
- Be vivid and specific — avoid generic clichés."""

FIRST_SEGMENT_PROMPT = """This is the BEGINNING of a brand new story. Establish the setting and introduce the adventurer.

The adventurer's first completed quest:
Title: {task_title}
{task_desc}

Write an opening story segment (2-3 sentences) that sets the scene and weaves this quest into the narrative."""

CONTINUATION_PROMPT = """Previous story so far:
---
{previous_segments}
---

The adventurer just completed a new quest:
Title: {task_title}
{task_desc}

Continue the story with the next segment (2-3 sentences), building on what came before and incorporating this quest as a plot event."""


def generate_story_segment(db: Session, task: Task, profile: Profile) -> str | None:
    if not ANTHROPIC_API_KEY:
        return None

    try:
        client = _get_client()
        genre = profile.genre_preference or "fantasy"
        genre_tone = GENRE_TONES.get(genre, GENRE_TONES["fantasy"])

        recent = (
            db.query(StorySegment)
            .order_by(StorySegment.created_at.desc())
            .limit(CONTEXT_WINDOW)
            .all()
        )
        recent.reverse()

        system = SYSTEM_PROMPT.format(genre_tone=genre_tone)
        task_desc = f"Description: {task.description}" if task.description else ""

        if not recent:
            user_msg = FIRST_SEGMENT_PROMPT.format(
                task_title=task.title, task_desc=task_desc
            )
        else:
            prev_text = "\n\n".join(seg.content for seg in recent)
            user_msg = CONTINUATION_PROMPT.format(
                previous_segments=prev_text,
                task_title=task.title,
                task_desc=task_desc,
            )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )

        content = response.content[0].text.strip()

        segment = StorySegment(
            task_id=task.id,
            content=content,
            genre=genre,
        )
        db.add(segment)
        db.commit()

        return content

    except Exception:
        traceback.print_exc()
        return None
