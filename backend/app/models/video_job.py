from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class VideoStage(str, Enum):
    NEW = "NEW"
    IDEA_GENERATING = "IDEA_GENERATING"
    IDEA_REVIEW = "IDEA_REVIEW"
    IDEA_APPROVED = "IDEA_APPROVED"
    SCRIPT_GENERATING = "SCRIPT_GENERATING"
    SCRIPT_REVIEW = "SCRIPT_REVIEW"
    SCRIPT_APPROVED = "SCRIPT_APPROVED"
    MANIM_GENERATING = "MANIM_GENERATING"
    QA_RUNNING = "QA_RUNNING"
    FINAL_REVIEW = "FINAL_REVIEW"
    FINAL_APPROVED = "FINAL_APPROVED"
    UPLOAD_REVIEW = "UPLOAD_REVIEW"
    UPLOADING = "UPLOADING"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    track: Mapped[str] = mapped_column(String(64))
    video_type: Mapped[str] = mapped_column(String(64))
    stage: Mapped[VideoStage] = mapped_column(SqlEnum(VideoStage), default=VideoStage.NEW)
    current_payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    rejection_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idea_card: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    script_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    research_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    manim_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    platform_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scheduled_publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
