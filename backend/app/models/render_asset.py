from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RenderAsset(Base):
    __tablename__ = "render_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String(1024))
    asset_metadata: Mapped[dict | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
