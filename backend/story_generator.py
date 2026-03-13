from __future__ import annotations

import traceback
from sqlalchemy.orm import Session

from config import GEMINI_API_KEY, ANTHROPIC_API_KEY
from models import Task, Profile, StorySegment

# Lazy clients to avoid import errors if a package is missing
_gemini_client = None
_anthropic_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not configured")
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


GENRE_TONES = {
    "fantasy": "high fantasy with magic, swords, and ancient prophecies. Think medieval quests and enchanted forests.",
    "sci-fi": "science fiction with advanced technology, space exploration, and futuristic societies.",
    "mystery": "a detective mystery with clues, suspense, and unexpected twists lurking around every corner.",
    "horror": "dark horror with creeping dread, ominous shadows, and supernatural threats.",
    "adventure": "a swashbuckling adventure with daring escapades, treasure hunts, and narrow escapes.",
    "comedy": "a comedic romp with witty banter, absurd situations, and lighthearted chaos.",
}

CONTEXT_WINDOW = 5

# System prompt for ongoing story (continuation + cliffhanger)
SYSTEM_PROMPT = """You are a master storyteller writing a serial {genre_tone} adventure in second person ("You").

CRITICAL RULES:
- Write EXACTLY one new paragraph (2-4 sentences). This paragraph must describe NEW events that happen AFTER the previous story text. Do NOT repeat, rephrase, or summarize what already happened.
- Turn the completed quest into a clear, specific plot event in the story. Use the quest title and description literally as inspiration (e.g. "do laundry" might become washing a blood-stained cloak, or "buy groceries" could become gathering supplies before a journey). The reader should recognize the real-world task reflected in the narrative.
- End this paragraph with a cliffhanger or a strong hook: a danger, a mystery, a decision, or a revelation that makes the reader want to know what happens next. Do NOT end with a resolved, calm moment.
- Write only the new paragraph. No meta-commentary, no "Chapter X", no game mechanics or quest titles in the text. Stay in second person and in genre."""

# For the very first segment
FIRST_SEGMENT_PROMPT = """This is the OPENING of a new story. Write exactly one paragraph (2-4 sentences) that:
1) Establishes the setting and the adventurer (second person "You") in a {genre_tone} world.
2) Weaves in the adventurer's first completed quest as a concrete story event. Use the quest title and description as direct inspiration (e.g. "do laundry" could be washing something significant; "buy groceries" could be gathering provisions). The reader should see the real task reflected in the scene.
3) Ends on a cliffhanger or hook—something unresolved that makes the reader want to continue (danger, mystery, or a new goal). Do not wrap up the scene; leave tension or curiosity.

Quest completed:
Title: {task_title}
{task_desc}

Write only the opening paragraph, nothing else."""

# For middle segments (continuation)
CONTINUATION_PROMPT = """The story so far (do NOT repeat or copy this; what follows is for context only):
---
{previous_segments}
---

The adventurer just completed another quest. Write the NEXT paragraph only (2-4 sentences):
1) Use this quest as a clear plot event in the narrative. Base the scene on the quest title and description (e.g. "do dishes" might become cleaning a weapon or clearing a table after a tense meeting). Make it specific and recognizable.
2) Advance the plot from where the story left off. Something new must happen in your paragraph.
3) End with a cliffhanger or hook—unresolved tension, a new threat, or a pivotal moment. Do not end with everything settled.

Quest just completed:
Title: {task_title}
{task_desc}

Write only the new paragraph. Do not repeat the previous text."""

# When the user marks this task as "Story ender" — conclude the narrative
CONCLUSION_SYSTEM_PROMPT = """You are a master storyteller writing the final paragraph of a {genre_tone} serial. Write in second person ("You").

RULES:
- Write one closing paragraph (3-5 sentences) that brings the current story arc to a satisfying end.
- Weave in the adventurer's final completed quest as a concrete story event (use the quest title/description as inspiration). This quest should feel like the last step that allows the conclusion.
- Resolve the main tension or bring the current adventure to a clear, satisfying close. The reader should feel the story has reached an ending, not another cliffhanger.
- No meta-commentary, no "The End" in the text. Just the final paragraph."""

CONCLUSION_PROMPT = """The story so far:
---
{previous_segments}
---

The adventurer just completed their final quest (use it as the last story beat):
Title: {task_title}
{task_desc}

Write the final paragraph of the story (3-5 sentences): a satisfying conclusion that incorporates this quest and closes the narrative. No cliffhanger—this is the ending."""


def _generate_via_gemini(system: str, user_msg: str) -> str | None:
    try:
        from google.genai import types
        client = _get_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=280,
                temperature=0.85,
            ),
        )
        if response and response.text:
            return response.text.strip()
    except Exception:
        traceback.print_exc()
    return None


def _generate_via_anthropic(system: str, user_msg: str) -> str | None:
    try:
        client = _get_anthropic_client()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=280,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        if response.content and len(response.content) > 0:
            return response.content[0].text.strip()
    except Exception:
        traceback.print_exc()
    return None


def generate_story_segment(db: Session, task: Task, profile: Profile) -> str | None:
    use_gemini = bool(GEMINI_API_KEY)
    use_anthropic = bool(ANTHROPIC_API_KEY)
    if not use_gemini and not use_anthropic:
        return None

    try:
        genre = profile.genre_preference or "fantasy"
        genre_tone = GENRE_TONES.get(genre, GENRE_TONES["fantasy"])

        recent = (
            db.query(StorySegment)
            .order_by(StorySegment.created_at.desc())
            .limit(CONTEXT_WINDOW)
            .all()
        )
        recent.reverse()

        task_desc = f"Description: {task.description}" if task.description else ""

        # Story ender: conclude the narrative
        if getattr(task, "story_ender", False) and recent:
            system = CONCLUSION_SYSTEM_PROMPT.format(genre_tone=genre_tone)
            prev_text = "\n\n".join(seg.content for seg in recent)
            user_msg = CONCLUSION_PROMPT.format(
                previous_segments=prev_text,
                task_title=task.title,
                task_desc=task_desc,
            )
        elif getattr(task, "story_ender", False) and not recent:
            # Edge case: first segment but marked as story ender — treat as single-paragraph story
            system = CONCLUSION_SYSTEM_PROMPT.format(genre_tone=genre_tone)
            user_msg = f"""The adventurer completed a single quest that will serve as the whole story. Write one short, self-contained paragraph (3-4 sentences) that tells a complete mini-story in second person, {genre_tone}, using this quest as the central event.

Quest: Title: {task.title}
{task_desc}

Write only the paragraph."""
        elif not recent:
            system = SYSTEM_PROMPT.format(genre_tone=genre_tone)
            user_msg = FIRST_SEGMENT_PROMPT.format(
                genre_tone=genre_tone,
                task_title=task.title,
                task_desc=task_desc,
            )
        else:
            system = SYSTEM_PROMPT.format(genre_tone=genre_tone)
            prev_text = "\n\n".join(seg.content for seg in recent)
            user_msg = CONTINUATION_PROMPT.format(
                previous_segments=prev_text,
                task_title=task.title,
                task_desc=task_desc,
            )

        content = None
        if use_gemini:
            content = _generate_via_gemini(system, user_msg)
        if content is None and use_anthropic:
            content = _generate_via_anthropic(system, user_msg)

        if not content:
            return None

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
