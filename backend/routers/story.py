import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import StorySegment, StoryArchive
from schemas import StorySegmentOut, StoryArchiveOut, ArchiveRequest, RenameArchiveRequest, RateSegmentRequest

router = APIRouter(prefix="/story", tags=["story"])


@router.get("", response_model=list[StorySegmentOut])
def get_story(db: Session = Depends(get_db)):
    segs = (
        db.query(StorySegment)
        .options(joinedload(StorySegment.task))
        .order_by(StorySegment.created_at.asc())
        .all()
    )
    results = []
    for s in segs:
        d = StorySegmentOut.model_validate(s).model_dump()
        d["task_title"] = s.task.title if s.task else None
        results.append(d)
    return results


@router.get("/archives", response_model=list[StoryArchiveOut])
def get_archives(db: Session = Depends(get_db)):
    archives = (
        db.query(StoryArchive)
        .order_by(StoryArchive.created_at.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "title": a.title,
            "created_at": a.created_at,
            "segments": json.loads(a.segments_json),
        }
        for a in archives
    ]


@router.post("/archive")
def archive_story(req: ArchiveRequest, db: Session = Depends(get_db)):
    segs = (
        db.query(StorySegment)
        .options(joinedload(StorySegment.task))
        .order_by(StorySegment.created_at.asc())
        .all()
    )
    if not segs:
        raise HTTPException(400, "No story segments to archive.")

    snapshot = [
        {
            "id": s.id,
            "task_id": s.task_id,
            "task_title": s.task.title if s.task else None,
            "content": s.content,
            "genre": s.genre,
            "created_at": s.created_at.isoformat(),
        }
        for s in segs
    ]

    db.add(StoryArchive(title=req.title.strip() or "Untitled Chapter", segments_json=json.dumps(snapshot)))
    db.query(StorySegment).delete()
    db.commit()
    return {"archived": True}


@router.put("/archives/{archive_id}")
def rename_archive(archive_id: int, req: RenameArchiveRequest, db: Session = Depends(get_db)):
    archive = db.query(StoryArchive).filter(StoryArchive.id == archive_id).first()
    if not archive:
        raise HTTPException(404, "Archive not found.")
    archive.title = req.title.strip() or archive.title
    db.commit()
    return {"renamed": True}


@router.delete("/archives/{archive_id}", status_code=204)
def delete_archive(archive_id: int, db: Session = Depends(get_db)):
    archive = db.query(StoryArchive).filter(StoryArchive.id == archive_id).first()
    if not archive:
        raise HTTPException(404, "Archive not found.")
    db.delete(archive)
    db.commit()


@router.post("/archives/{archive_id}/narrate")
def narrate_archive(archive_id: int, db: Session = Depends(get_db)):
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        raise HTTPException(400, "Gemini API key not configured. Set GEMINI_API_KEY in backend/.env to enable narration.")

    archive = db.query(StoryArchive).filter(StoryArchive.id == archive_id).first()
    if not archive:
        raise HTTPException(404, "Archive not found.")

    segments = json.loads(archive.segments_json)
    if not segments:
        raise HTTPException(400, "This chapter has no story segments to narrate.")

    # Build the full narration script
    lines = [archive.title, ""]
    for i, seg in enumerate(segments):
        quest_label = f"Quest: {seg['task_title']}" if seg.get("task_title") else ""
        if quest_label:
            lines.append(quest_label)
        lines.append(f"Chapter {i + 1}.")
        lines.append(seg["content"])
        lines.append("")

    story_text = "\n".join(lines).strip()

    from story_generator import generate_tts_audio
    wav_bytes = generate_tts_audio(story_text)
    if wav_bytes is None:
        raise HTTPException(500, "Audio generation failed. Check that GEMINI_API_KEY is valid and the TTS model is available.")

    return Response(content=wav_bytes, media_type="audio/wav")


@router.put("/segments/{segment_id}/rate")
def rate_segment(segment_id: int, req: RateSegmentRequest, db: Session = Depends(get_db)):
    seg = db.query(StorySegment).filter(StorySegment.id == segment_id).first()
    if not seg:
        raise HTTPException(404, "Segment not found.")
    seg.rating = req.rating
    seg.feedback = req.feedback if req.feedback and req.feedback.strip() else None
    db.commit()
    return {"rated": True}


@router.post("/reset", status_code=204)
def reset_story(db: Session = Depends(get_db)):
    db.query(StorySegment).delete()
    db.commit()
