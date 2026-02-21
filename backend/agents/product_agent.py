"""Product Agent — Inception/MVP/Risks from requirements (BA-style aligned)."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision


SYSTEM_PROMPT = """You are a Product Manager agent in a software development pipeline.
Your job is to produce an Inception/MVP document from a list of requirements.

CRITICAL RULES:
- Analyze ALL provided requirements and define the MVP scope for a PILOT.
- included_reqs + excluded_reqs MUST cover ALL requirement IDs provided.
- requirement_ids MUST list ALL requirement IDs provided.
- Identify between 3 and 6 realistic risks for the project.
- Define at least 3 clear, measurable success criteria.
- ALL text content MUST be written in Spanish.
- The id field must always be exactly "INC-001".
- Risk IDs must follow the format RISK-001, RISK-002, etc.
- The "impact" field must be exactly "high", "medium", or "low".
- Do NOT invent requirements that are not in the input.
- Respond ONLY with valid JSON, no extra text.

Required JSON format:

{
  "id": "INC-001",
  "title": "Inception document title",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "mvp_scope": {
    "included_reqs": ["REQ-001"],
    "excluded_reqs": ["REQ-002"],
    "justification": "Clear MVP justification"
  },
  "risks": [
    {
      "id": "RISK-001",
      "description": "Risk description in Spanish",
      "impact": "high",
      "mitigation": "Mitigation strategy in Spanish"
    }
  ],
  "success_criteria": [
    "Measurable success criterion in Spanish"
  ]
}
"""


async def run_product_agent(state: PipelineState) -> dict:
    """Receive requirements and generate INC-001 with MVP scope, risks and success criteria."""

    run_id = state["run_id"]
    requirements = state.get("requirements") or {}

    await log_decision(
        run_id,
        "product_agent",
        "started",
        {"input_reqs": len(requirements.get("artifacts", []))}
    )

    prompt = f"""
Generate the Inception/MVP document based on the following requirements.

Requirements (JSON):
{json.dumps(requirements, indent=2, ensure_ascii=False)}

Instructions:
- Define the MVP as a pilot: include what is necessary for field viability and minimum actionable value.
- Non-functional requirements MAY be included if they are critical enablers.
- Exclude what can be deferred without compromising the pilot.
- In "mvp_scope.justification" briefly explain why the MVP is coherent for a pilot.
- Ensure included_reqs + excluded_reqs cover ALL requirement_ids.
- Do NOT invent new requirements.
- Return ONLY the JSON with the exact required structure.
"""

    # Inject feedback exactly like BA agent
    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"""

## Reviewer feedback (apply it in your response)
{feedback}
"""

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    req_ids = result.get("requirement_ids") or []

    await save_artifact(
        run_id=run_id,
        artifact_id=result.get("id", "INC-001"),
        agent="product_agent",
        artifact_type="inception",
        content=result,
        parent_ids=req_ids,
    )

    await log_decision(
        run_id,
        "product_agent",
        "completed",
        {
            "inception_id": result.get("id", "INC-001"),
            "included_reqs": len(result.get("mvp_scope", {}).get("included_reqs", [])),
            "excluded_reqs": len(result.get("mvp_scope", {}).get("excluded_reqs", [])),
            "risks_identified": len(result.get("risks", [])),
            "success_criteria": len(result.get("success_criteria", [])),
        }
    )

    return {"inception": result}
