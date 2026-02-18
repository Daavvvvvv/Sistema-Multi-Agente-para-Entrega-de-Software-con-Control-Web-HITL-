"""Design Agent — ER and Sequence diagrams in Mermaid."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """You are a Software Design agent in a software development pipeline.
Your job is to generate two diagrams from the project artifacts:
1. An ER (Entity-Relationship) diagram
2. A Sequence diagram

RULES:
- Use valid Mermaid.js syntax.
- The ER diagram must model the domain entities derived from the requirements.
- The Sequence diagram must illustrate the main user flow from the user stories.
- Reference the requirement and story IDs that each diagram covers.
- Respond ONLY with valid JSON, no extra text."""

USER_PROMPT_TEMPLATE = """Given the following software artifacts, generate an ER diagram and a Sequence diagram using Mermaid.js syntax.

## Requirements
{requirements}

## Inception / MVP
{inception}

## User Stories
{user_stories}

## Test Cases
{test_cases}

Respond with this exact JSON structure:
{{
  "er_diagram": {{
    "mermaid_code": "erDiagram\\n    ENTITY1 ||--o{{ ENTITY2 : has\\n    ...",
    "referenced_reqs": ["REQ-001", "REQ-002"],
    "referenced_stories": [],
    "description": "Brief description of what the ER diagram represents"
  }},
  "sequence_diagram": {{
    "mermaid_code": "sequenceDiagram\\n    actor User\\n    User->>System: action\\n    ...",
    "referenced_reqs": [],
    "referenced_stories": ["US-001", "US-002"],
    "description": "Brief description of what the sequence diagram represents"
  }}
}}

IMPORTANT: Use valid Mermaid.js syntax. Escape newlines as \\n in the mermaid_code strings. Respond ONLY with JSON."""


async def run_design_agent(state: PipelineState) -> dict:
    """Receive all artifacts and generate ER + sequence diagrams as Mermaid code."""
    run_id = state["run_id"]
    requirements = state.get("requirements") or {}
    inception = state.get("inception") or {}
    user_stories = state.get("user_stories") or {}
    test_cases = state.get("test_cases") or {}

    await log_decision(run_id, "design_agent", "started", {
        "input_reqs": len(requirements.get("artifacts", [])),
        "input_stories": len(user_stories.get("artifacts", [])),
    })

    prompt = USER_PROMPT_TEMPLATE.format(
        requirements=json.dumps(requirements, indent=2, ensure_ascii=False),
        inception=json.dumps(inception, indent=2, ensure_ascii=False),
        user_stories=json.dumps(user_stories, indent=2, ensure_ascii=False),
        test_cases=json.dumps(test_cases, indent=2, ensure_ascii=False),
    )

    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"\n\n## HITL Feedback (address this in your output)\n{feedback}"

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # Save ER diagram
    er = result.get("er_diagram", {})
    if er:
        parent_ids = er.get("referenced_reqs", []) + er.get("referenced_stories", [])
        await save_artifact(
            run_id=run_id,
            artifact_id="DIAG-ER",
            agent="design_agent",
            artifact_type="diagram_er",
            content=er,
            parent_ids=parent_ids,
        )

    # Save Sequence diagram
    seq = result.get("sequence_diagram", {})
    if seq:
        parent_ids = seq.get("referenced_reqs", []) + seq.get("referenced_stories", [])
        await save_artifact(
            run_id=run_id,
            artifact_id="DIAG-SEQ",
            agent="design_agent",
            artifact_type="diagram_sequence",
            content=seq,
            parent_ids=parent_ids,
        )

    await log_decision(run_id, "design_agent", "completed", {
        "has_er": bool(er),
        "has_sequence": bool(seq),
    })

    return {"diagrams": result}
