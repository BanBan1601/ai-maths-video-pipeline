from pydantic import BaseModel
from typing import Optional


class DashboardResponse(BaseModel):
    total_videos: int
    published: int
    pending_approvals: int
    stage_counts: dict[str, int]
    workers: list[str]
    system_status: str


class VideoJobResponse(BaseModel):
    id: int
    slug: str
    title: str
    track: str
    video_type: str
    stage: str
    idea_card: Optional[dict] = None
    script_data: Optional[dict] = None
    preview_path: Optional[str] = None
    created_at: str
    updated_at: str


class QAReportResponse(BaseModel):
    qa_type: str
    passed: bool
    issues: list
    repair_actions: list


class PipelineBoardResponse(BaseModel):
    board: dict[str, list]
