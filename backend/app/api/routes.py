from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
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
from app.services.upload_service import UploadService

import uuid

router = APIRouter(prefix="/api")
upload_service = UploadService()


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: DbSession):
    """System status overview."""
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
    # Enrich with approvals
    approvals = db.query(Approval).filter(Approval.video_job_id == video_id).all()
    result["approvals"] = [
        {
            "gate": a.gate,
            "decision": a.decision,
            "feedback": a.feedback,
            "created_at": str(a.created_at),
        }
        for a in approvals
    ]
    # Enrich with sources
    sources = db.query(SourceRecord).filter(SourceRecord.video_job_id == video_id).all()
    result["sources"] = [
        {
            "id": s.id,
            "title": s.title,
            "url": s.url,
            "trust_score": s.trust_score,
            "source_type": s.source_type,
        }
        for s in sources
    ]
    # Enrich with QA reports
    qa_reports = db.query(QAReport).filter(QAReport.video_job_id == video_id).all()
    result["qa_reports"] = [
        {
            "qa_type": q.qa_type,
            "passed": q.passed,
            "issues": q.issues,
            "repair_actions": q.repair_actions,
        }
        for q in qa_reports
    ]
    return result


@router.post("/videos")
def create_video(payload: VideoJobCreate, db: DbSession):
    slug = f"{payload.title.lower().replace(' ', '-')[:40]}-{uuid.uuid4().hex[:6]}"
    job = VideoJob(
        slug=slug,
        title=payload.title,
        track=payload.track,
        video_type=payload.video_type,
        stage=VideoStage.NEW,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _video_to_dict(job)


# ── Pipeline board ─────────────────────────────────────────────────────────────

@router.get("/pipeline")
def get_pipeline(db: DbSession):
    """Kanban-style pipeline board data."""
    all_jobs = db.query(VideoJob).order_by(VideoJob.updated_at.desc()).all()
    board: dict[str, list] = {}
    for job in all_jobs:
        stage = str(job.stage.value)
        if stage not in board:
            board[stage] = []
        board[stage].append({
            "id": job.id,
            "title": job.title,
            "track": job.track,
            "video_type": job.video_type,
            "slug": job.slug,
            "updated_at": str(job.updated_at),
        })
    return board


# ── Idea approval gate ─────────────────────────────────────────────────────────

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
def approve_upload(video_id: int, payload: ApprovalDecision, db: DbSession):
    job = _get_job_or_404(db, video_id)
    _record_approval(db, job, "UPLOAD", payload.decision, payload.feedback)
    if payload.decision == "approve":
        _transition_job(db, job, VideoStage.UPLOADING)
        # TODO: trigger upload task
    else:
        _transition_job(db, job, VideoStage.REJECTED)
    db.commit()
    return _video_to_dict(job)


# ── Autonomous idea proposal ───────────────────────────────────────────────────

@router.post("/ideas/propose")
def propose_ideas(db: DbSession, bg: BackgroundTasks, count: int = 1):
    """Trigger autonomous idea proposal. The worker will create VideoJob records."""
    from app.workers.tasks import task_generate_idea
    for _ in range(count):
        task_generate_idea.delay()
    return {"queued": count, "message": "Idea generation tasks dispatched"}


# ── QA ────────────────────────────────────────────────────────────────────────

@router.get("/videos/{video_id}/qa")
def get_qa_report(video_id: int, db: DbSession):
    reports = db.query(QAReport).filter(QAReport.video_job_id == video_id).all()
    return [
        {
            "qa_type": r.qa_type,
            "passed": r.passed,
            "issues": r.issues,
            "repair_actions": r.repair_actions,
            "metrics": r.metrics,
            "created_at": str(r.created_at),
        }
        for r in reports
    ]


# ── Platforms ──────────────────────────────────────────────────────────────────

@router.get("/platforms/status")
def platforms_status():
    return {
        "youtube": upload_service.youtube_status(),
        "instagram": upload_service.instagram_status(),
    }


# ── Sources ────────────────────────────────────────────────────────────────────

@router.get("/videos/{video_id}/sources")
def get_sources(video_id: int, db: DbSession):
    sources = db.query(SourceRecord).filter(SourceRecord.video_job_id == video_id).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "url": s.url,
            "doi": s.doi,
            "trust_score": s.trust_score,
            "source_type": s.source_type,
            "authors": s.authors,
        }
        for s in sources
    ]


# ── Helpers ────────────────────────────────────────────────────────────────────

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


def _record_approval(
    db: Session, job: VideoJob, gate: str, decision: str, feedback: Optional[str]
) -> None:
    approval = Approval(
        video_job_id=job.id,
        gate=gate,
        decision=decision,
        feedback=feedback,
    )
    db.add(approval)


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
        "created_at": str(job.created_at),
        "updated_at": str(job.updated_at),
    }


def _trigger_script_generation(video_id: int) -> None:
    from app.workers.tasks import task_generate_script
    task_generate_script.delay(video_id)


def _trigger_manim_generation(video_id: int) -> None:
    from app.workers.tasks import task_generate_manim
    task_generate_manim.delay(video_id)
