from pydantic import BaseModel
from typing import Optional


class VideoJobCreate(BaseModel):
    title: str
    track: str
    video_type: str


class ApprovalDecision(BaseModel):
    decision: str  # "approve" or "reject"
    feedback: Optional[str] = None
    gate: Optional[str] = None  # for backward compat
