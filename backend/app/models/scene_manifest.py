from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SceneManifest(Base):
    __tablename__ = "scene_manifests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    scenes: Mapped[Optional[dict]] = mapped_column(JSON, default=list)  # list of scene dicts
    manim_code: Mapped[Optional[str]] = mapped_column(String(65535), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
