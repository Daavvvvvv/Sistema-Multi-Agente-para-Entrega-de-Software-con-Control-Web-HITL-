"""Analyst Agent — User stories from requirements + inception."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """You are a Business Analyst agent in a software development pipeline.
Your job is to generate clear, testable User Stories from Requirements and Inception/MVP information.

RULES:
- Generate user stories based on the provided requirements and MVP scope.
- Each user story MUST reference at least one requirement ID in requirement_ids.
- Prefer MVP included requirements first (if provided).
- IDs must be sequential: US-001, US-002, US-003...
- Each story must include acceptance criteria using DADO/CUANDO/ENTONCES (Given/When/Then).
- Provide at least 2 acceptance scenarios per story:
  1) Positive (happy path)
  2) Negative (error/invalid case)
- Use the story format: "Como <actor>, quiero <capacidad>, para <beneficio>."
- Provide realistic priority: high | medium | low
- Provide a simple estimation string (e.g., "S", "M", "L").
- Do NOT invent features unrelated to the requirements.
- Respond ONLY with valid JSON, no extra text."""

USER_PROMPT_TEMPLATE = """Given the following project artifacts, generate user stories with acceptance criteria.

## Requirements (source of truth)
{requirements}

## Inception / MVP (scope, risks, success criteria)
{inception}

Return this exact JSON structure:
{{
  "artifacts": [
    {{
      "id": "US-001",
      "title": "Short story title",
      "requirement_ids": ["REQ-001"],
      "story": "Como <actor>, quiero <capacidad>, para <beneficio>.",
      "acceptance_criteria": [
        "Escenario 1 (positivo): DADO ..., CUANDO ..., ENTONCES ...",
        "Escenario 2 (negativo): DADO ..., CUANDO ..., ENTONCES ..."
      ],
      "priority": "high",
      "estimation": "M"
    }}
  ]
}}

Guidelines:
- Create at least 1 user story per functional requirement (combine only if truly necessary).
- Make acceptance criteria specific and testable, using DADO/CUANDO/ENTONCES.
- Include exactly 2 scenarios per story: one positive and one negative.
- Keep titles short and descriptive.
- If MVP scope lists included_reqs, prioritize those and do NOT create stories for excluded_reqs.
- Respond ONLY with JSON."""

async def run_analyst_agent(state: PipelineState) -> dict:
    """Receive REQs + INC and generate US-001, US-002... with acceptance criteria."""
    run_id = state["run_id"]
    requirements = state.get("requirements") or {}
    inception = state.get("inception") or {}

    await log_decision(run_id, "analyst_agent", "started", {
        "input_reqs": len(requirements.get("artifacts", [])),
        "has_inception": bool(inception),
    })

    prompt = USER_PROMPT_TEMPLATE.format(
        requirements=json.dumps(requirements, indent=2, ensure_ascii=False),
        inception=json.dumps(inception, indent=2, ensure_ascii=False),
    )

    # If there's HITL feedback from the previous gate, include it so the agent fixes issues
    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"\n\n## HITL Feedback (address this in your output)\n{feedback}"

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # Save each user story as an artifact
    for us in result.get("artifacts", []):
        req_ids = us.get("requirement_ids", []) or []
        await save_artifact(
            run_id=run_id,
            artifact_id=us["id"],
            agent="analyst_agent",
            artifact_type="user_story",
            content=us,
            parent_ids=req_ids,
        )

    await log_decision(run_id, "analyst_agent", "completed", {
        "user_stories_generated": len(result.get("artifacts", [])),
    })

    return {"user_stories": result}
