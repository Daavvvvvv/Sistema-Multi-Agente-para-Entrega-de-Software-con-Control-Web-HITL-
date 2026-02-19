"""Product Agent — Inception/MVP/Risks from requirements."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """You are a Product Manager agent in a software development pipeline.
Your job is to produce an Inception/MVP document from a list of requirements.

RULES:
- Analyze ALL provided requirements and define the MVP scope.
- Classify each requirement as included or excluded from the MVP, with a brief justification.
- Identify between 3 and 6 realistic risks for the project.
- Define at least 3 clear, measurable success criteria.
- ALL text content (titles, descriptions, justifications, risks, criteria) MUST be written in Spanish.
- The id field must always be exactly "INC-001".
- Risk IDs must follow the format RISK-001, RISK-002, etc.
- The "impact" field of each risk must be exactly "high", "medium", or "low".
- Do NOT invent requirements that are not in the input.
- Respond ONLY with valid JSON, no extra text.

Required JSON format:

{
  "id": "INC-001",
  "title": "Titulo del documento de Inception",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "mvp_scope": {
    "included_reqs": ["REQ-001"],
    "excluded_reqs": ["REQ-002"],
    "justification": "Justificacion clara de por que estos requisitos forman el MVP"
  },
  "risks": [
    {
      "id": "RISK-001",
      "description": "Descripcion del riesgo en espanol",
      "impact": "high",
      "mitigation": "Estrategia de mitigacion en espanol"
    }
  ],
  "success_criteria": [
    "Criterio de exito medible en espanol"
  ]
}
"""

USER_PROMPT_TEMPLATE = """Based on the following requirements, generate the Inception/MVP document.

## Requirements
{requirements}

Define the MVP scope by selecting which requirements are essential for the first deliverable
and which can be deferred. Identify the main project risks and success criteria.

Return this exact JSON structure:
{{
  "id": "INC-001",
  "title": "Titulo del documento de Inception",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "mvp_scope": {{
    "included_reqs": ["REQ-001"],
    "excluded_reqs": ["REQ-002"],
    "justification": "Justificacion clara del MVP"
  }},
  "risks": [
    {{
      "id": "RISK-001",
      "description": "Descripcion del riesgo",
      "impact": "high",
      "mitigation": "Estrategia de mitigacion"
    }}
  ],
  "success_criteria": [
    "Criterio de exito medible"
  ]
}}

Guidelines:
- Include in the MVP the high-priority functional requirements that form the core product value.
- Defer to post-MVP the low-priority or non-functional requirements that can be added later.
- requirement_ids must list ALL requirement IDs provided (both included and excluded).
- included_reqs + excluded_reqs together must cover ALL requirement IDs.
- Identify between 3 and 6 risks. Each risk must have a concrete mitigation strategy.
- Success criteria must be specific and measurable (not vague).
- Respond ONLY with JSON."""


async def run_product_agent(state: PipelineState) -> dict:
    """Receive requirements and generate INC-001 with MVP scope, risks and success criteria."""
    run_id = state["run_id"]
    requirements = state.get("requirements") or {}

    await log_decision(run_id, "product_agent", "started", {
        "input_reqs": len(requirements.get("artifacts", [])),
    })

    prompt = USER_PROMPT_TEMPLATE.format(
        requirements=json.dumps(requirements, indent=2, ensure_ascii=False),
    )

    # If there is HITL feedback from the previous gate, include it so the agent corrects its output
    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"\n\n## Feedback del revisor HITL (corrige esto en tu respuesta)\n{feedback}"

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # Save INC-001 as a single artifact; parent_ids are the referenced requirements
    req_ids = result.get("requirement_ids") or []
    await save_artifact(
        run_id=run_id,
        artifact_id=result.get("id", "INC-001"),
        agent="product_agent",
        artifact_type="inception",
        content=result,
        parent_ids=req_ids,
    )

    await log_decision(run_id, "product_agent", "completed", {
        "inception_id": result.get("id", "INC-001"),
        "included_reqs": len(result.get("mvp_scope", {}).get("included_reqs", [])),
        "excluded_reqs": len(result.get("mvp_scope", {}).get("excluded_reqs", [])),
        "risks_identified": len(result.get("risks", [])),
        "success_criteria": len(result.get("success_criteria", [])),
    })

    return {"inception": result}
