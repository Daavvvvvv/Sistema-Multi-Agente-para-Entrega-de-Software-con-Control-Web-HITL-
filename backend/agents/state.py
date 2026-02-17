from __future__ import annotations

from typing import Optional, TypedDict


class PipelineState(TypedDict):
    run_id: str
    brief: str
    current_stage: str
    requirements: Optional[dict]
    inception: Optional[dict]
    user_stories: Optional[dict]
    test_cases: Optional[dict]
    diagrams: Optional[dict]
    hitl_status: Optional[str]   # pending | approved | rejected | changes
    hitl_feedback: Optional[str]
    error: Optional[str]
    retry_count: int
