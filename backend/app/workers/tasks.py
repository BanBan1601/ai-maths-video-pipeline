from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.workers.celery_app import celery_app
from app.services.topic_engine import TopicEngine
from app.services.script_service import ScriptService
from app.services.research_service import ResearchService
from app.services.qa_service import QAService
from app.services.manim_generator import ManimGenerator


_topic_engine = TopicEngine()
_script_service = ScriptService()
_research_service = ResearchService()
_qa_service = QAService()
_manim_gen = ManimGenerator()


def _get_db():
    from app.db.session import SessionLocal
    return SessionLocal()


@celery_app.task(name="app.workers.tasks.task_generate_idea", bind=True, max_retries=3)
def task_generate_idea(self) -> dict:
    """Propose a new video idea and persist it to DB."""
    db = _get_db()
    try:
        from app.models.video_job import VideoJob, VideoStage
        from app.models.source_record import SourceRecord

        candidate = _topic_engine.propose()

        # Fetch references
        sources = _research_service.retrieve_sources(
            topic=candidate.title,
            queries=candidate.reference_queries,
        )

        slug = f"{candidate.title.lower().replace(' ', '-')[:35]}-{uuid.uuid4().hex[:6]}"
        idea_card = {
            "title": candidate.title,
            "hook": candidate.hook,
            "track": candidate.track,
            "subtopic": candidate.subtopic,
            "video_type": candidate.video_type,
            "audience": candidate.audience,
            "visual_richness": candidate.visual_richness,
            "novelty": candidate.novelty,
            "reference_count": len(sources),
            "proposed_at": datetime.utcnow().isoformat(),
        }

        job = VideoJob(
            slug=slug,
            title=candidate.title,
            track=candidate.track,
            video_type=candidate.video_type,
            stage=VideoStage.IDEA_REVIEW,
            idea_card=idea_card,
        )
        db.add(job)
        db.flush()

        # Persist sources
        for src in sources:
            sr = SourceRecord(
                video_job_id=job.id,
                title=src.title,
                authors=src.authors,
                doi=getattr(src, "doi", None),
                url=src.url,
                source_type=src.source_type,
                trust_score=src.trust_score,
            )
            db.add(sr)

        db.commit()
        db.refresh(job)
        return {"job_id": job.id, "title": job.title, "stage": job.stage.value}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_generate_script", bind=True, max_retries=3)
def task_generate_script(self, video_id: int) -> dict:
    """Generate script for an approved idea."""
    db = _get_db()
    try:
        from app.models.video_job import VideoJob, VideoStage
        from app.models.source_record import SourceRecord
        from app.models.claim import Claim
        from app.core.state_machine import transition

        job = db.get(VideoJob, video_id)
        if not job:
            return {"error": f"Video {video_id} not found"}

        # Transition to SCRIPT_GENERATING
        job.stage = transition(job.stage, VideoStage.SCRIPT_GENERATING)
        job.updated_at = datetime.utcnow()
        db.commit()

        # Get sources
        sources = db.query(SourceRecord).filter(SourceRecord.video_job_id == video_id).all()
        source_dicts = [
            {"title": s.title, "url": s.url, "trust_score": s.trust_score} for s in sources
        ]

        script_data = _script_service.build_short_script(
            title=job.title,
            video_type=job.video_type,
            idea_card=job.idea_card,
            sources=source_dicts,
        )

        # Persist claims
        for claim_info in script_data.get("claims", []):
            claim = Claim(
                video_job_id=video_id,
                claim_text=claim_info.get("text", ""),
                claim_type=claim_info.get("type", "intuition"),
                confidence=0.9,
            )
            db.add(claim)

        # Update job
        job.script_data = script_data
        job.stage = transition(job.stage, VideoStage.SCRIPT_REVIEW)
        job.updated_at = datetime.utcnow()
        db.commit()
        return {
            "job_id": video_id,
            "stage": job.stage.value,
            "word_count": script_data.get("word_count", 0),
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_generate_manim", bind=True, max_retries=2)
def task_generate_manim(self, video_id: int) -> dict:
    """Generate Manim code from approved script."""
    db = _get_db()
    try:
        from app.models.video_job import VideoJob, VideoStage
        from app.models.scene_manifest import SceneManifest
        from app.core.state_machine import transition

        job = db.get(VideoJob, video_id)
        if not job or not job.script_data:
            return {"error": f"Video {video_id} not found or has no script"}

        job.stage = transition(job.stage, VideoStage.MANIM_GENERATING)
        job.updated_at = datetime.utcnow()
        db.commit()

        scenes = job.script_data.get("scenes", [])
        manim_code = _manim_gen.generate_from_scene_manifest(title=job.title, scenes=scenes)

        manifest = SceneManifest(
            video_job_id=video_id,
            scenes=scenes,
            manim_code=manim_code,
        )
        db.add(manifest)
        job.manim_code = manim_code
        job.stage = transition(job.stage, VideoStage.QA_RUNNING)
        job.updated_at = datetime.utcnow()
        db.commit()

        # Immediately queue QA
        task_run_qa.delay(video_id)
        return {
            "job_id": video_id,
            "stage": job.stage.value,
            "manim_code_lines": len(manim_code.splitlines()),
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_run_qa", bind=True, max_retries=2)
def task_run_qa(self, video_id: int) -> dict:
    """Run layout QA on generated Manim scenes."""
    db = _get_db()
    try:
        from app.models.video_job import VideoJob, VideoStage
        from app.models.qa_report import QAReport
        from app.core.state_machine import transition

        job = db.get(VideoJob, video_id)
        if not job:
            return {"error": f"Video {video_id} not found"}

        # Build placeholder scene metrics from script narration word counts
        scenes = job.script_data.get("scenes", []) if job.script_data else []
        scene_metrics = {
            "objects": [
                {
                    "id": f"scene_{s.get('scene_id', i)}_text",
                    "word_count": len(s.get("narration", "").split()),
                }
                for i, s in enumerate(scenes)
            ]
        }
        qa_result = _qa_service.run_render_qa(scene_metrics)

        report = QAReport(
            video_job_id=video_id,
            qa_type="layout",
            passed=qa_result["passed"],
            issues=qa_result["issues"],
            repair_actions=qa_result["repair_actions"],
            metrics=qa_result["metrics"],
        )
        db.add(report)

        if qa_result["passed"]:
            job.stage = transition(job.stage, VideoStage.FINAL_REVIEW)
        else:
            has_errors = any(
                i.get("severity") == "error" for i in qa_result["issues"]
            )
            if not has_errors:
                job.stage = transition(job.stage, VideoStage.FINAL_REVIEW)
            # else: remain in QA_RUNNING for manual review

        job.updated_at = datetime.utcnow()
        db.commit()
        return {
            "job_id": video_id,
            "qa_passed": qa_result["passed"],
            "stage": job.stage.value,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.seed_video_job")
def seed_video_job() -> dict:
    """Beat-scheduled task: keep at least 3 ideas in IDEA_REVIEW."""
    db = _get_db()
    try:
        from app.models.video_job import VideoJob, VideoStage
        from sqlalchemy import func

        count_pending = (
            db.query(func.count(VideoJob.id))
            .filter(VideoJob.stage == VideoStage.IDEA_REVIEW)
            .scalar()
        )
        needed = max(0, 3 - count_pending)
        for _ in range(needed):
            task_generate_idea.delay()
        return {"seeded": needed, "already_pending": count_pending}
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.task_upload_video", bind=True, max_retries=2)
def task_upload_video(self, video_id: int) -> dict:
    """Upload rendered video to YouTube and/or Instagram."""
    db = _get_db()
    try:
        from app.models.video_job import VideoJob, VideoStage
        from app.core.state_machine import transition
        from app.services.youtube_service import YouTubeService
        from app.services.instagram_service import InstagramService
        import os

        job = db.get(VideoJob, video_id)
        if not job:
            return {"error": f"Video {video_id} not found"}

        meta = job.platform_metadata or {}
        results: dict = {}

        yt_svc = YouTubeService()
        ig_svc = InstagramService()

        # ── YouTube ────────────────────────────────────────────────────────────
        yt_status = yt_svc.get_status()
        if yt_status.get("connected") and job.preview_path and os.path.exists(job.preview_path):
            try:
                yt_result = yt_svc.upload_video(
                    file_path=job.preview_path,
                    title=meta.get("youtube_title", job.title),
                    description=meta.get("youtube_description", ""),
                    tags=meta.get("tags", []),
                    scheduled_at=job.scheduled_publish_at,
                )
                results["youtube"] = yt_result
                meta["youtube_url"] = yt_result.get("youtube_url")
                meta["youtube_video_id"] = yt_result.get("youtube_video_id")
            except Exception as yt_err:
                results["youtube_error"] = str(yt_err)

        # ── Instagram ──────────────────────────────────────────────────────────
        ig_status = ig_svc.get_status()
        if ig_status.get("connected"):
            # Instagram requires a public URL — derive from preview_path filename
            if job.preview_path:
                filename = job.preview_path.split("/")[-1]
                public_url = f"http://localhost:8000/renders/{filename}"
                try:
                    ig_result = ig_svc.upload_video(
                        video_url=public_url,
                        caption=meta.get("instagram_caption", job.title),
                    )
                    results["instagram"] = ig_result
                    meta["instagram_url"] = ig_result.get("instagram_url")
                except Exception as ig_err:
                    results["instagram_error"] = str(ig_err)

        # ── Persist results ────────────────────────────────────────────────────
        job.platform_metadata = meta
        if results.get("youtube") or results.get("instagram"):
            job.stage = transition(job.stage, VideoStage.PUBLISHED)
        job.updated_at = datetime.utcnow()
        db.commit()

        return {"job_id": video_id, "results": results, "stage": job.stage.value}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
