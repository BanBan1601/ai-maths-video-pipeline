from __future__ import annotations

from app.models.video_job import VideoStage

VALID_TRANSITIONS: dict[VideoStage, list[VideoStage]] = {
    VideoStage.NEW: [VideoStage.IDEA_GENERATING],
    VideoStage.IDEA_GENERATING: [VideoStage.IDEA_REVIEW, VideoStage.REJECTED],
    VideoStage.IDEA_REVIEW: [VideoStage.IDEA_APPROVED, VideoStage.REJECTED],
    VideoStage.IDEA_APPROVED: [VideoStage.SCRIPT_GENERATING],
    VideoStage.SCRIPT_GENERATING: [VideoStage.SCRIPT_REVIEW, VideoStage.REJECTED],
    VideoStage.SCRIPT_REVIEW: [VideoStage.SCRIPT_APPROVED, VideoStage.REJECTED],
    VideoStage.SCRIPT_APPROVED: [VideoStage.MANIM_GENERATING],
    VideoStage.MANIM_GENERATING: [VideoStage.QA_RUNNING, VideoStage.REJECTED],
    VideoStage.QA_RUNNING: [VideoStage.FINAL_REVIEW, VideoStage.MANIM_GENERATING],
    VideoStage.FINAL_REVIEW: [VideoStage.FINAL_APPROVED, VideoStage.REJECTED],
    VideoStage.FINAL_APPROVED: [VideoStage.UPLOAD_REVIEW],
    VideoStage.UPLOAD_REVIEW: [VideoStage.UPLOADING, VideoStage.REJECTED],
    VideoStage.UPLOADING: [VideoStage.PUBLISHED, VideoStage.REJECTED],
    VideoStage.PUBLISHED: [],
    VideoStage.REJECTED: [VideoStage.IDEA_GENERATING],  # allow re-entry after rejection
}


class InvalidTransitionError(Exception):
    pass


def transition(current: VideoStage, target: VideoStage) -> VideoStage:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition from {current} to {target}. Allowed: {allowed}"
        )
    return target
