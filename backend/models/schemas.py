from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# --- Request models ---

class CreateRunRequest(BaseModel):
    brief: str


class HitlDecisionRequest(BaseModel):
    feedback: Optional[str] = None


# --- Artifact sub-models ---

class Requirement(BaseModel):
    id: str
    title: str
    description: str
    type: str  # functional | non_functional
    priority: str  # high | medium | low
    actors: list[str] = []


class RequirementsOutput(BaseModel):
    artifacts: list[Requirement]
    domain_summary: str = ""
    assumptions: list[str] = []


class MvpScope(BaseModel):
    included_reqs: list[str] = []
    excluded_reqs: list[str] = []
    justification: str = ""


class Risk(BaseModel):
    id: str
    description: str
    impact: str  # high | medium | low
    mitigation: str = ""


class InceptionOutput(BaseModel):
    id: str
    title: str = ""
    phase: str = ""           # "MVP / Piloto" | "Versión 1.0" | "Versión Futura"
    requirement_ids: list[str] = []
    mvp_scope: MvpScope
    risks: list[Risk] = []
    success_criteria: list[str] = []


class InceptionsOutput(BaseModel):
    inceptions: list[InceptionOutput] = []


class UserStory(BaseModel):
    id: str
    title: str
    requirement_ids: list[str] = []
    story: str  # Como..., quiero..., para...
    acceptance_criteria: list[str] = []
    priority: str = "medium"
    estimation: str = ""


class UserStoriesOutput(BaseModel):
    artifacts: list[UserStory]


class TestCase(BaseModel):
    id: str
    title: str
    user_story_ids: list[str] = []
    requirement_ids: list[str] = []
    preconditions: list[str] = []
    steps: list[str] = []
    expected_result: str = ""
    type: str = "positive"  # positive | negative


class TestCasesOutput(BaseModel):
    artifacts: list[TestCase]


class DiagramData(BaseModel):
    mermaid_code: str = ""
    referenced_reqs: list[str] = []
    referenced_stories: list[str] = []
    description: str = ""


class DiagramsOutput(BaseModel):
    er_diagram: DiagramData
    sequence_diagram: DiagramData


# --- Response models ---

class RunResponse(BaseModel):
    id: str
    brief: str
    status: str
    current_stage: str
    created_at: str
    updated_at: str


class ArtifactResponse(BaseModel):
    id: str
    run_id: str
    agent: str
    type: str
    content: dict
    parent_ids: list[str]
    created_at: str


class DecisionLogEntry(BaseModel):
    id: int
    run_id: str
    agent: str
    action: str
    details: dict
    timestamp: str


class HitlGateResponse(BaseModel):
    id: int
    run_id: str
    stage: str
    status: str
    feedback: Optional[str]
    created_at: str
    resolved_at: Optional[str]
