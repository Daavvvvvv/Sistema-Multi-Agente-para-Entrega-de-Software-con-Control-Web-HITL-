"""Product Agent — Inception/MVP from requirements."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """You are a Product Manager agent in a software development pipeline.
Your job is to create an Inception/MVP document from the requirements.

RULES:
- Define the MVP scope: which requirements are included and which are excluded.
- Justify inclusion/exclusion decisions.
- Identify risks with impact levels and mitigations.
- Define clear success criteria for the MVP.
- The document ID must be INC-001.
- ALL text content (justifications, descriptions, criteria) MUST be written in Spanish.
- Respond ONLY with valid JSON, no extra text."""

USER_PROMPT_TEMPLATE = """Based on the following requirements, create an Inception/MVP document.

## Requirements
{requirements}

Respond with this exact JSON structure:
{{
  "id": "INC-001",
  "mvp_scope": {{
    "included_reqs": ["REQ-001", "REQ-002"],
    "excluded_reqs": ["REQ-005"],
    "justification": "Explicacion en espanol de por que se seleccionaron estos requerimientos para el MVP"
  }},
  "risks": [
    {{
      "id": "RISK-001",
      "description": "Descripcion del riesgo en espanol",
      "impact": "high",
      "mitigation": "Como mitigar este riesgo, en espanol"
    }}
  ],
  "success_criteria": ["Criterio de exito 1 en espanol", "Criterio 2"]
}}

Guidelines:
- Include ALL high-priority requirements in MVP scope.
- Exclude low-priority or complex requirements with justification.
- Identify at least 3 risks with realistic mitigations.
- Define at least 3 measurable success criteria.
- ALL descriptions, justifications, and criteria MUST be in Spanish.
- Respond ONLY with JSON."""


async def run_product_agent(state: PipelineState) -> dict:
    """Receive REQs and generate INC-001 with MVP scope, risks, prioritization."""
    run_id = state["run_id"]
    requirements = state.get("requirements") or {}

    await log_decision(run_id, "product_agent", "started", {
        "input_reqs": len(requirements.get("artifacts", [])),
    })

    prompt = USER_PROMPT_TEMPLATE.format(
        requirements=json.dumps(requirements, indent=2, ensure_ascii=False),
    )

    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"\n\n## HITL Feedback (address this in your output)\n{feedback}"

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # Save inception as a single artifact
    req_ids = result.get("mvp_scope", {}).get("included_reqs", [])
    await save_artifact(
        run_id=run_id,
        artifact_id=result.get("id", "INC-001"),
        agent="product_agent",
        artifact_type="inception",
        content=result,
        parent_ids=req_ids,
    )

    await log_decision(run_id, "product_agent", "completed", {
        "included_reqs": len(req_ids),
        "excluded_reqs": len(result.get("mvp_scope", {}).get("excluded_reqs", [])),
        "risks_identified": len(result.get("risks", [])),
    })

    return {"inception": result}
