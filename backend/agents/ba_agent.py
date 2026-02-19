"""BA Agent — Requirements extraction from brief."""

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """You are a Software Requirements Analyst agent in a software development pipeline.
Your job is to extract explicit requirements from the provided brief.

RULES:
- Extract ONLY explicit requirements from the text. Do NOT infer or invent information.
- Do NOT add extra text outside the JSON.
- Respond ONLY with valid JSON using double quotes.
- The "type" field must be either "functional" or "non_functional".
- The "priority" field must be "high", "medium", or "low".
- Generate a unique short ID for each requirement (e.g. REQ-001, REQ-002, ...).
- ALL text content (titles, descriptions, domain_summary, assumptions) MUST be written in Spanish.
- Respond ONLY with valid JSON, no extra text.

Required JSON format:

{
  "artifacts": [
    {
      "id": "REQ-001",
      "title": "Titulo corto en espanol",
      "description": "Descripcion detallada en espanol",
      "type": "functional",
      "priority": "medium",
      "actors": []
    }
  ],
  "domain_summary": "Resumen del dominio en espanol",
  "assumptions": ["Suposicion en espanol"]
}
"""


async def run_ba_agent(state: PipelineState) -> dict:
    """Read the brief and generate REQ-001, REQ-002... as structured JSON."""
    run_id = state["run_id"]
    brief = state.get("brief", "")

    await log_decision(run_id, "ba_agent", "started", {"brief_length": len(brief)})

    prompt = f"""
Analiza el siguiente brief y extrae los requisitos:
{brief}
Responde SOLO con JSON.
"""

    # Si hay feedback de HITL, agregarlo para que el agente corrija
    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"\n\n## Feedback del revisor (corrige esto en tu respuesta)\n{feedback}"

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # Guardar artefactos en DB
    for item in result.get("artifacts", []):
        await save_artifact(
            run_id=run_id,
            artifact_id=item["id"],
            agent="ba_agent",
            artifact_type="requirement",
            content=item,
            parent_ids=[],
        )

    await log_decision(run_id, "ba_agent", "completed", {
        "requirements_generated": len(result.get("artifacts", [])),
    })

    return {"requirements": result}
