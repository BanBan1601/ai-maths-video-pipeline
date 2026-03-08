from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.core.state_machine import transition, InvalidTransitionError
from app.models.approval import Approval
from app.models.claim import Claim
from app.models.qa_report import QAReport
from app.models.scene_manifest import SceneManifest
from app.models.source_record import SourceRecord
from app.models.video_job import VideoJob, VideoStage
from app.schemas.responses import DashboardResponse
from app.schemas.video_job import ApprovalDecision, VideoJobCreate
from app.services.metadata_service import MetadataService
from app.services.youtube_service import YouTubeService
from app.services.instagram_service import InstagramService

import uuid

router = APIRouter(prefix="/api")
_metadata_svc = MetadataService()
_youtube_svc = YouTubeService()
_instagram_svc = InstagramService()


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: DbSession):
    stage_counts = (
        db.query(VideoJob.stage, func.count(VideoJob.id))
        .group_by(VideoJob.stage)
        .all()
    )
    pending_approvals = db.query(VideoJob).filter(
        VideoJob.stage.in_([
            VideoStage.IDEA_REVIEW,
            VideoStage.SCRIPT_REVIEW,
            VideoStage.FINAL_REVIEW,
            VideoStage.UPLOAD_REVIEW,
        ])
    ).count()
    total = db.query(VideoJob).count()
    published = db.query(VideoJob).filter(VideoJob.stage == VideoStage.PUBLISHED).count()
    return DashboardResponse(
        total_videos=total,
        published=published,
        pending_approvals=pending_approvals,
        stage_counts={str(s.value): c for s, c in stage_counts},
        workers=["scheduler", "research", "script", "render", "qa", "audio", "compose", "upload"],
        system_status="running",
    )


# ── Videos CRUD ───────────────────────────────────────────────────────────────

@router.get("/videos")
def list_videos(db: DbSession, stage: Optional[str] = None, limit: int = 50):
    q = db.query(VideoJob)
    if stage:
        q = q.filter(VideoJob.stage == VideoStage(stage))
    jobs = q.order_by(VideoJob.created_at.desc()).limit(limit).all()
    return [_video_to_dict(j) for j in jobs]


@router.get("/videos/{video_id}")
def get_video(video_id: int, db: DbSession):
    job = db.get(VideoJob, video_id)
    if not job:
        raise HTTPException(404, "Video not found")
    result = _video_to_dict(job)
    approvals = db.query(Approval).filter(Approval.video_job_id == video_id).all()
    result["approvals"] = [
        {"gate": a.gate, "decision": a.decision, "feedback": a.feedback, "created_at": str(a.created_at)}
        for a in approvals
    ]
    sources = db.query(SourceRecord).filter(SourceRecord.video_job_id == video_id).all()
    result["sources"] = [
        {"id": s.id, "title": s.title, "url": s.url, "trust_score": s.trust_score, "source_type": s.source_type}
        for s in sources
    ]
    qa_reports = db.query(QAReport).filter(QAReport.video_job_id == video_id).all()
    result["qa_reports"] = [
        {"qa_type": q.qa_type, "passed": q.passed, "issues": q.issues, "repair_actions": q.repair_actions}
        for q in qa_reports
    ]
    return result


@router.post("/videos")
def create_video(payload: VideoJobCreate, db: DbSession):
    slug = f"{payload.title.lower().replace(' ', '-')[:40]}-{uuid.uuid4().hex[:6]}"
    job = VideoJob(
        slug=slug, title=payload.title, track=payload.track,
        video_type=payload.video_type, stage=VideoStage.NEW,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _video_to_dict(job)


# ── Pipeline board ─────────────────────────────────────────────────────────────

@router.get("/pipeline")
def get_pipeline(db: DbSession):
    all_jobs = db.query(VideoJob).order_by(VideoJob.updated_at.desc()).all()
    board: dict[str, list] = {}
    for job in all_jobs:
        stage = str(job.stage.value)
        if stage not in board:
            board[stage] = []
        board[stage].append({
            "id": job.id, "title": job.title, "track": job.track,
            "video_type": job.video_type, "slug": job.slug, "updated_at": str(job.updated_at),
        })
    return board


# ── Approval gates ─────────────────────────────────────────────────────────────

@router.post("/videos/{video_id}/approve-idea")
def approve_idea(video_id: int, payload: ApprovalDecision, db: DbSession, bg: BackgroundTasks):
    job = _get_job_or_404(db, video_id)
    _record_approval(db, job, "IDEA", payload.decision, payload.feedback)
    if payload.decision == "approve":
        _transition_job(db, job, VideoStage.IDEA_APPROVED)
        bg.add_task(_trigger_script_generation, video_id)
    else:
        _transition_job(db, job, VideoStage.REJECTED)
    db.commit()
    return _video_to_dict(job)


@router.post("/videos/{video_id}/approve-script")
def approve_script(video_id: int, payload: ApprovalDecision, db: DbSession, bg: BackgroundTasks):
    job = _get_job_or_404(db, video_id)
    _record_approval(db, job, "SCRIPT", payload.decision, payload.feedback)
    if payload.decision == "approve":
        _transition_job(db, job, VideoStage.SCRIPT_APPROVED)
        bg.add_task(_trigger_manim_generation, video_id)
    else:
        _transition_job(db, job, VideoStage.REJECTED)
    db.commit()
    return _video_to_dict(job)


@router.post("/videos/{video_id}/approve-final")
def approve_final(video_id: int, payload: ApprovalDecision, db: DbSession):
    job = _get_job_or_404(db, video_id)
    _record_approval(db, job, "FINAL", payload.decision, payload.feedback)
    if payload.decision == "approve":
        _transition_job(db, job, VideoStage.FINAL_APPROVED)
        _transition_job(db, job, VideoStage.UPLOAD_REVIEW)
    else:
        _transition_job(db, job, VideoStage.REJECTED)
    db.commit()
    return _video_to_dict(job)


@router.post("/videos/{video_id}/approve-upload")
def approve_upload(video_id: int, payload: ApprovalDecision, db: DbSession, bg: BackgroundTasks):
    job = _get_job_or_404(db, video_id)
    _record_approval(db, job, "UPLOAD", payload.decision, payload.feedback)
    if payload.decision == "approve":
        _transition_job(db, job, VideoStage.UPLOADING)
        bg.add_task(_trigger_upload, video_id)
    else:
        _transition_job(db, job, VideoStage.REJECTED)
    db.commit()
    return _video_to_dict(job)


# ── Auto-approve (single video) ────────────────────────────────────────────────

@router.post("/videos/{video_id}/auto-approve")
def auto_approve(video_id: int, db: DbSession, bg: BackgroundTasks):
    """Auto-approve whichever gate the video is currently waiting at."""
    job = _get_job_or_404(db, video_id)
    stage = job.stage

    if stage == VideoStage.IDEA_REVIEW:
        _record_approval(db, job, "IDEA", "approve", "auto-approved")
        _transition_job(db, job, VideoStage.IDEA_APPROVED)
        db.commit()
        bg.add_task(_trigger_script_generation, video_id)
    elif stage == VideoStage.SCRIPT_REVIEW:
        _record_approval(db, job, "SCRIPT", "approve", "auto-approved")
        _transition_job(db, job, VideoStage.SCRIPT_APPROVED)
        db.commit()
        bg.add_task(_trigger_manim_generation, video_id)
    elif stage == VideoStage.FINAL_REVIEW:
        _record_approval(db, job, "FINAL", "approve", "auto-approved")
        _transition_job(db, job, VideoStage.FINAL_APPROVED)
        _transition_job(db, job, VideoStage.UPLOAD_REVIEW)
        db.commit()
    elif stage == VideoStage.UPLOAD_REVIEW:
        _record_approval(db, job, "UPLOAD", "approve", "auto-approved")
        _transition_job(db, job, VideoStage.UPLOADING)
        db.commit()
        bg.add_task(_trigger_upload, video_id)
    else:
        raise HTTPException(400, f"Video is in stage {stage.value} — no approval gate to auto-approve")

    return _video_to_dict(job)


# ── Bulk-approve (all videos at a stage) ──────────────────────────────────────

@router.post("/bulk-approve")
def bulk_approve(stage: str, db: DbSession, bg: BackgroundTasks):
    """Approve all videos waiting at a given stage."""
    try:
        target_stage = VideoStage(stage)
    except ValueError:
        raise HTTPException(400, f"Unknown stage: {stage}")

    jobs = db.query(VideoJob).filter(VideoJob.stage == target_stage).all()
    approved = 0
    for job in jobs:
        try:
            if target_stage == VideoStage.IDEA_REVIEW:
                _record_approval(db, job, "IDEA", "approve", "bulk-approved")
                _transition_job(db, job, VideoStage.IDEA_APPROVED)
                db.commit()
                bg.add_task(_trigger_script_generation, job.id)
            elif target_stage == VideoStage.SCRIPT_REVIEW:
                _record_approval(db, job, "SCRIPT", "approve", "bulk-approved")
                _transition_job(db, job, VideoStage.SCRIPT_APPROVED)
                db.commit()
                bg.add_task(_trigger_manim_generation, job.id)
            elif target_stage == VideoStage.FINAL_REVIEW:
                _record_approval(db, job, "FINAL", "approve", "bulk-approved")
                _transition_job(db, job, VideoStage.FINAL_APPROVED)
                _transition_job(db, job, VideoStage.UPLOAD_REVIEW)
                db.commit()
            elif target_stage == VideoStage.UPLOAD_REVIEW:
                _record_approval(db, job, "UPLOAD", "approve", "bulk-approved")
                _transition_job(db, job, VideoStage.UPLOADING)
                db.commit()
                bg.add_task(_trigger_upload, job.id)
            approved += 1
        except Exception:
            db.rollback()
    return {"count": approved, "stage": stage}


# ── Preview URL ────────────────────────────────────────────────────────────────

@router.get("/videos/{video_id}/preview-url")
def get_preview_url(video_id: int, db: DbSession):
    job = _get_job_or_404(db, video_id)
    if job.preview_path:
        # preview_path is a filesystem path like /data/renders/slug.mp4
        # We serve it via StaticFiles mounted at /renders → /data/renders
        filename = job.preview_path.split("/")[-1]
        return {"has_video": True, "video_url": f"/renders/{filename}"}
    return {"has_video": False, "video_url": None, "stage": job.stage.value}


# ── Metadata generation ────────────────────────────────────────────────────────

@router.post("/videos/{video_id}/generate-metadata")
def generate_metadata(video_id: int, db: DbSession):
    job = _get_job_or_404(db, video_id)
    if not job.script_data:
        raise HTTPException(400, "Script not yet generated for this video")
    metadata = _metadata_svc.generate(title=job.title, script_data=job.script_data)
    job.platform_metadata = metadata
    job.updated_at = datetime.utcnow()
    db.commit()
    return {"metadata": metadata}


@router.put("/videos/{video_id}/metadata")
def update_metadata(video_id: int, payload: dict, db: DbSession):
    job = _get_job_or_404(db, video_id)
    existing = job.platform_metadata or {}
    existing.update(payload)
    job.platform_metadata = existing
    job.updated_at = datetime.utcnow()
    db.commit()
    return _video_to_dict(job)


# ── Schedule ───────────────────────────────────────────────────────────────────

@router.put("/videos/{video_id}/schedule")
def set_schedule(video_id: int, payload: dict, db: DbSession):
    job = _get_job_or_404(db, video_id)
    scheduled_at_str = payload.get("scheduled_publish_at")
    if scheduled_at_str:
        try:
            dt = datetime.fromisoformat(scheduled_at_str.replace("Z", "+00:00"))
            job.scheduled_publish_at = dt
        except ValueError:
            raise HTTPException(400, "Invalid datetime format — use ISO 8601")
    else:
        job.scheduled_publish_at = None
    job.updated_at = datetime.utcnow()
    db.commit()
    return _video_to_dict(job)


# ── Upload trigger ─────────────────────────────────────────────────────────────

@router.post("/videos/{video_id}/upload")
def trigger_upload(video_id: int, db: DbSession, bg: BackgroundTasks):
    job = _get_job_or_404(db, video_id)
    if job.stage not in (VideoStage.UPLOADING, VideoStage.UPLOAD_REVIEW):
        raise HTTPException(400, f"Video must be in UPLOADING or UPLOAD_REVIEW stage, got {job.stage.value}")
    bg.add_task(_trigger_upload, video_id)
    return {"queued": True, "video_id": video_id}


# ── Platform connections ────────────────────────────────────────────────────────

@router.get("/platforms/youtube/connect")
def youtube_connect():
    """Redirect user to Google OAuth consent screen."""
    try:
        auth_url = _youtube_svc.get_auth_url()
        return RedirectResponse(url=auth_url)
    except RuntimeError as e:
        raise HTTPException(500, str(e))


@router.get("/platforms/youtube/callback")
def youtube_callback(code: str, db: DbSession):
    """Handle OAuth2 redirect — exchange code for token."""
    try:
        _youtube_svc.exchange_code(code)
        return RedirectResponse(url="http://localhost:3000/platforms?yt=connected")
    except Exception as e:
        raise HTTPException(500, f"OAuth exchange failed: {e}")


@router.get("/platforms/youtube/status")
def youtube_status():
    return _youtube_svc.get_status()


@router.get("/platforms/instagram/status")
def instagram_status():
    return _instagram_svc.get_status()


@router.get("/platforms/status")
def platforms_status():
    return {
        "youtube": _youtube_svc.get_status(),
        "instagram": _instagram_svc.get_status(),
    }


# ── Autonomous idea proposal ────────────────────────────────────────────────────

@router.post("/ideas/propose")
def propose_ideas(db: DbSession, bg: BackgroundTasks, count: int = 1):
    from app.workers.tasks import task_generate_idea
    for _ in range(count):
        task_generate_idea.delay()
    return {"queued": count, "message": "Idea generation tasks dispatched"}


# ── QA ─────────────────────────────────────────────────────────────────────────

@router.get("/videos/{video_id}/qa")
def get_qa_report(video_id: int, db: DbSession):
    reports = db.query(QAReport).filter(QAReport.video_job_id == video_id).all()
    return [
        {
            "qa_type": r.qa_type, "passed": r.passed, "issues": r.issues,
            "repair_actions": r.repair_actions, "metrics": r.metrics, "created_at": str(r.created_at),
        }
        for r in reports
    ]


# ── Sources ─────────────────────────────────────────────────────────────────────

@router.get("/videos/{video_id}/sources")
def get_sources(video_id: int, db: DbSession):
    sources = db.query(SourceRecord).filter(SourceRecord.video_job_id == video_id).all()
    return [
        {
            "id": s.id, "title": s.title, "url": s.url, "doi": s.doi,
            "trust_score": s.trust_score, "source_type": s.source_type, "authors": s.authors,
        }
        for s in sources
    ]


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_job_or_404(db: Session, video_id: int) -> VideoJob:
    job = db.get(VideoJob, video_id)
    if not job:
        raise HTTPException(404, "Video not found")
    return job


def _transition_job(db: Session, job: VideoJob, target: VideoStage) -> None:
    try:
        job.stage = transition(job.stage, target)
        job.updated_at = datetime.utcnow()
    except InvalidTransitionError as e:
        raise HTTPException(400, str(e))


def _record_approval(db: Session, job: VideoJob, gate: str, decision: str, feedback: Optional[str]) -> None:
    db.add(Approval(video_job_id=job.id, gate=gate, decision=decision, feedback=feedback))


def _video_to_dict(job: VideoJob) -> dict:
    return {
        "id": job.id,
        "slug": job.slug,
        "title": job.title,
        "track": job.track,
        "video_type": job.video_type,
        "stage": job.stage.value,
        "idea_card": job.idea_card,
        "script_data": job.script_data,
        "preview_path": job.preview_path,
        "platform_metadata": job.platform_metadata,
        "scheduled_publish_at": str(job.scheduled_publish_at) if job.scheduled_publish_at else None,
        "created_at": str(job.created_at),
        "updated_at": str(job.updated_at),
    }


def _trigger_script_generation(video_id: int) -> None:
    from app.workers.tasks import task_generate_script
    task_generate_script.delay(video_id)


def _trigger_manim_generation(video_id: int) -> None:
    from app.workers.tasks import task_generate_manim
    task_generate_manim.delay(video_id)


def _trigger_upload(video_id: int) -> None:
    from app.workers.tasks import task_upload_video
    task_upload_video.delay(video_id)
