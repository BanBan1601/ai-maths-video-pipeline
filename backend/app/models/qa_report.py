from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class QAReport(Base):
    __tablename__ = "qa_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    qa_type: Mapped[str] = mapped_column(String(64))  # layout/audio/script/final
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    issues: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    repair_actions: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
