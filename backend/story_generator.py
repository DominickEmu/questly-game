from __future__ import annotations

import json
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

# System prompt for the FIRST segment (opening of a new story)
FIRST_SEGMENT_SYSTEM = """You are a master storyteller opening a brand new serial {genre_tone} adventure in second person ("You").

RULES:
- Write exactly one complete paragraph of 3–4 full sentences. Every sentence must be finished — no sentence may be left incomplete.
- Establish the adventurer ("You") and the world vividly in the opening sentence.
- Weave the completed quest into the scene as a concrete story event (e.g. "clean stinky sock" becomes scrubbing a cursed relic; "buy groceries" becomes gathering provisions before a journey). The real-world task should be recognizable in the narrative.
- End the paragraph on a clear cliffhanger or hook — a danger spotted, a mystery uncovered, a decision looming. The reader must feel compelled to continue.
- Write ONLY the paragraph. No titles, no chapter numbers, no meta-commentary."""

# System prompt for CONTINUATION segments
CONTINUATION_SYSTEM = """You are a master storyteller continuing a serial {genre_tone} adventure in second person ("You").

RULES:
- Write exactly one complete paragraph of 3–4 full sentences. Every sentence must be finished — do NOT cut off mid-sentence.
- Your paragraph must continue DIRECTLY from where the previous story text ended. Do not repeat, rephrase, or summarize what already happened.
- Weave the newly completed quest into the scene as a concrete plot event (e.g. "do dishes" might become cleaning a weapon; "send email" might become dispatching a messenger). The real-world task should be recognizable.
- End on a cliffhanger or strong hook — unresolved tension, a new threat, a revelation. Do not resolve everything peacefully.
- Write ONLY the new paragraph. No previous text, no titles, no meta-commentary."""

# For the very first segment
FIRST_SEGMENT_PROMPT = """The adventurer has just completed their very first quest. Write the opening paragraph of their story.

Quest completed:
Title: {task_title}
{task_desc}

Remember: 3–4 complete sentences, second person, {genre_tone} setting, end on a cliffhanger. Write only the paragraph."""

# For middle segments (continuation)
CONTINUATION_PROMPT = """The story so far — read this for context, do NOT repeat it in your response:
---
{previous_segments}
---

The adventurer just completed another quest. Write the NEXT paragraph that continues directly from the story above.

Quest just completed:
Title: {task_title}
{task_desc}

Remember: 3–4 complete sentences, advance the plot, end on a cliffhanger. Write only the new paragraph."""

# When the user marks this task as "Story ender" — conclude the narrative
CONCLUSION_SYSTEM = """You are a master storyteller writing the final paragraph of a {genre_tone} serial. Write in second person ("You").

RULES:
- Write one closing paragraph of 4–5 complete sentences. Every sentence must be finished.
- Continue directly from where the previous story text ended.
- Weave the final completed quest into the scene as the decisive last act (use the quest title/description as inspiration).
- Bring the story to a satisfying, emotionally resonant close. Resolve the central tension. Do NOT end on a cliffhanger.
- Write ONLY the final paragraph. No titles, no "The End", no meta-commentary."""

CONCLUSION_PROMPT = """The story so far — read this for context, do NOT repeat it:
---
{previous_segments}
---

The adventurer just completed their final quest. Write the closing paragraph that brings this story to a satisfying end.

Final quest:
Title: {task_title}
{task_desc}

Remember: 4–5 complete sentences, resolve the story, no cliffhanger. Write only the closing paragraph."""


def _build_feedback_context(db: Session) -> str:
    """Build a feedback block from liked/disliked story segments."""
    rated = (
        db.query(StorySegment)
        .filter(StorySegment.rating != 0, StorySegment.feedback.isnot(None))
        .order_by(StorySegment.created_at.desc())
        .limit(10)
        .all()
    )
    if not rated:
        return ""
    likes = [s.feedback for s in rated if s.rating == 1 and s.feedback]
    dislikes = [s.feedback for s in rated if s.rating == -1 and s.feedback]
    lines = []
    if dislikes:
        lines.append("READER FEEDBACK — avoid these story elements:")
        lines.extend(f"- {fb}" for fb in dislikes)
    if likes:
        lines.append("READER FEEDBACK — keep doing these things:")
        lines.extend(f"- {fb}" for fb in likes)
    return "\n".join(lines)


def _build_personal_context(profile: Profile) -> str:
    """Build a personal-context block from profile interests and life variables."""
    parts = []
    if profile.interests:
        try:
            data = json.loads(profile.interests)
            likes = data.get("likes", [])
            dislikes = data.get("dislikes", [])
            if likes:
                parts.append(f"The adventurer enjoys: {', '.join(likes)}.")
            if dislikes:
                parts.append(f"The adventurer dislikes: {', '.join(dislikes)}.")
        except (json.JSONDecodeError, TypeError):
            pass
    if profile.life_variables:
        try:
            variables = json.loads(profile.life_variables)
            if variables:
                lines = [f"- {v['name']} ({v.get('role', 'character')}): {v.get('description', '')}" for v in variables]
                parts.append("Key characters in the adventurer's world:\n" + "\n".join(lines))
        except (json.JSONDecodeError, TypeError):
            pass
    if getattr(profile, "story_elements", None):
        parts.append(f"Extra story directions from the adventurer:\n{profile.story_elements}")
    return "\n".join(parts) if parts else ""


def _generate_via_gemini(system: str, user_msg: str) -> str | None:
    try:
        from google.genai import types
        client = _get_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=600,
                temperature=0.9,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
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
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        if response.content and len(response.content) > 0:
            return response.content[0].text.strip()
    except Exception:
        traceback.print_exc()
    return None


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Wrap raw PCM bytes from Gemini TTS in a WAV container using Python's wave module."""
    import io, wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)  # 2 bytes = 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def generate_tts_audio(story_text: str) -> bytes | None:
    """
    Generate WAV audio for the given story text using Gemini TTS.
    Returns raw WAV bytes, or None on failure.
    Voice: Charon — deep and resonant, perfect for a dramatic narrator.
    """
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai as _genai
        from google.genai import types as _types

        client = _genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=story_text,
            config=_types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=_types.SpeechConfig(
                    voice_config=_types.VoiceConfig(
                        prebuilt_voice_config=_types.PrebuiltVoiceConfig(
                            voice_name="Charon",
                        )
                    )
                ),
            ),
        )
        raw = response.candidates[0].content.parts[0].inline_data.data
        # google-genai SDK returns raw bytes directly — no base64 decoding needed
        pcm_bytes = raw if isinstance(raw, bytes) else bytes(raw)
        return _pcm_to_wav(pcm_bytes)
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

        personal_ctx = _build_personal_context(profile)
        personal_block = (
            f"\n\nPERSONAL CONTEXT (weave these details naturally when relevant — "
            f"do not force every detail into every paragraph):\n{personal_ctx}"
            if personal_ctx else ""
        )

        feedback_ctx = _build_feedback_context(db)
        feedback_block = f"\n\n{feedback_ctx}" if feedback_ctx else ""

        recent = (
            db.query(StorySegment)
            .order_by(StorySegment.created_at.desc())
            .limit(CONTEXT_WINDOW)
            .all()
        )
        recent.reverse()

        task_desc = f"Description: {task.description}" if task.description else ""

        prev_text = "\n\n".join(seg.content for seg in recent) if recent else ""

        # Story ender: conclude the narrative
        if getattr(task, "story_ender", False) and recent:
            system = CONCLUSION_SYSTEM.format(genre_tone=genre_tone) + personal_block + feedback_block
            user_msg = CONCLUSION_PROMPT.format(
                previous_segments=prev_text,
                task_title=task.title,
                task_desc=task_desc,
            )
        elif getattr(task, "story_ender", False) and not recent:
            # Edge case: first and only segment, user wants a conclusion — write a self-contained story
            system = CONCLUSION_SYSTEM.format(genre_tone=genre_tone) + personal_block + feedback_block
            user_msg = f"""The adventurer completed a single quest. Write one self-contained paragraph (4–5 complete sentences) in second person, {genre_tone}, that tells a brief complete story using this quest as the central event. End with a sense of resolution, not a cliffhanger.

Quest:
Title: {task.title}
{task_desc}

Write only the paragraph."""
        elif not recent:
            system = FIRST_SEGMENT_SYSTEM.format(genre_tone=genre_tone) + personal_block + feedback_block
            user_msg = FIRST_SEGMENT_PROMPT.format(
                genre_tone=genre_tone,
                task_title=task.title,
                task_desc=task_desc,
            )
        else:
            system = CONTINUATION_SYSTEM.format(genre_tone=genre_tone) + personal_block + feedback_block
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
