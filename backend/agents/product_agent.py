"""Product Agent — Multiple Inception/MVP/Risks documents from requirements."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision


SYSTEM_PROMPT = """You are a Product Manager agent in a software development pipeline.
Your job is to produce MULTIPLE Inception documents from a list of requirements, organized by delivery phases.

CRITICAL RULES:
- Generate exactly 3 inception documents covering different delivery phases:
    * INC-001: MVP / Piloto — contains ONLY requirements with priority "high".
    * INC-002: Versión 1.0  — contains ONLY requirements with priority "medium".
    * INC-003: Versión Futura — contains ONLY requirements with priority "low".
- ASSIGNMENT IS STRICTLY BY PRIORITY FIELD. Do NOT reassign a requirement to a different inception
  than what its priority dictates. This rule overrides any other consideration.
- Every requirement ID provided MUST appear in exactly ONE inception (no duplicates, no omissions).
  The union of all included_reqs across all inceptions MUST equal ALL requirement IDs provided.
- Each inception has its own mvp_scope, risks, and success_criteria.
- The "included_reqs" for each inception must list ONLY the IDs whose priority matches that phase.
- The "excluded_reqs" for each inception must list ALL IDs assigned to the OTHER two inceptions.
- Identify between 2 and 4 realistic risks per inception.
- Define at least 2 measurable success criteria per inception.
- ALL text content MUST be written in Spanish.
- Risk IDs must be unique across ALL inceptions: RISK-001, RISK-002, etc. (do not reset per inception).
- The "impact" field must be exactly "high", "medium", or "low".
- Do NOT invent requirements that are not in the input.
- Respond ONLY with valid JSON, no extra text.

Required JSON format:

{
  "inceptions": [
    {
      "id": "INC-001",
      "title": "MVP / Piloto: <short title>",
      "phase": "MVP / Piloto",
      "requirement_ids": ["REQ-001", "REQ-002"],
      "mvp_scope": {
        "included_reqs": ["REQ-001"],
        "excluded_reqs": ["REQ-002"],
        "justification": "Justification in Spanish"
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
    },
    {
      "id": "INC-002",
      "title": "Versión 1.0: <short title>",
      "phase": "Versión 1.0",
      "requirement_ids": ["REQ-003"],
      "mvp_scope": {
        "included_reqs": ["REQ-003"],
        "excluded_reqs": [],
        "justification": "Justification in Spanish"
      },
      "risks": [...],
      "success_criteria": [...]
    },
    {
      "id": "INC-003",
      "title": "Versión Futura: <short title>",
      "phase": "Versión Futura",
      "requirement_ids": ["REQ-004"],
      "mvp_scope": {
        "included_reqs": ["REQ-004"],
        "excluded_reqs": [],
        "justification": "Justification in Spanish"
      },
      "risks": [...],
      "success_criteria": [...]
    }
  ]
}
"""


async def run_product_agent(state: PipelineState) -> dict:
    """Receive requirements and generate INC-001, INC-002, INC-003 covering different delivery phases."""

    run_id = state["run_id"]
    requirements = state.get("requirements") or {}

    await log_decision(
        run_id,
        "product_agent",
        "started",
        {"input_reqs": len(requirements.get("artifacts", []))}
    )

    # Pre-classify requirements by priority so the prompt is explicit
    artifacts = requirements.get("artifacts", [])
    high_ids   = [r["id"] for r in artifacts if r.get("priority") == "high"]
    medium_ids = [r["id"] for r in artifacts if r.get("priority") == "medium"]
    low_ids    = [r["id"] for r in artifacts if r.get("priority") == "low"]

    prompt = f"""
Generate 3 Inception documents (INC-001, INC-002, INC-003) based on the following requirements.

Requirements (JSON):
{json.dumps(requirements, indent=2, ensure_ascii=False)}

MANDATORY ASSIGNMENT — do NOT deviate from this:
- INC-001 (MVP / Piloto)   → included_reqs MUST be exactly: {json.dumps(high_ids)}
- INC-002 (Versión 1.0)    → included_reqs MUST be exactly: {json.dumps(medium_ids)}
- INC-003 (Versión Futura) → included_reqs MUST be exactly: {json.dumps(low_ids)}

Instructions:
- Use the lists above as-is for included_reqs. Do NOT move IDs between inceptions.
- excluded_reqs for each inception = all IDs NOT in its own included_reqs list.
- Write risks and success_criteria relevant to the scope of each phase.
- Do NOT invent requirements not present in the input.
- Return ONLY the JSON with the exact required structure.
"""

    # Inject HITL feedback if a reviewer requested changes
    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"""

## Reviewer feedback (apply it in your response)
{feedback}
"""

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # Save each inception document as a separate artifact
    inceptions = result.get("inceptions", [])
    total_included = 0
    total_risks = 0

    for inc in inceptions:
        req_ids = inc.get("requirement_ids") or []
        await save_artifact(
            run_id=run_id,
            artifact_id=inc.get("id", "INC-???"),
            agent="product_agent",
            artifact_type="inception",
            content=inc,
            parent_ids=req_ids,
        )
        total_included += len(inc.get("mvp_scope", {}).get("included_reqs", []))
        total_risks += len(inc.get("risks", []))

    await log_decision(
        run_id,
        "product_agent",
        "completed",
        {
            "inceptions_generated": len(inceptions),
            "inception_ids": [inc.get("id") for inc in inceptions],
            "total_reqs_covered": total_included,
            "total_risks_identified": total_risks,
        }
    )

    return {"inception": result}
