from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(64))  # definition/theorem/intuition/historical/application/analogy
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # comma-separated source record IDs
    review_status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
