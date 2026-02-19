"""BA Agent — Requirements extraction from brief."""

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """You are a Software Requirements Analyst (BA) agent in a SDLC pipeline.
Your job is to extract well-formed engineering requirements from the provided brief.

CRITICAL RULES:
- Produce requirements that describe SYSTEM CAPABILITIES or SYSTEM CONSTRAINTS relevant to building the game.
- Do NOT just restate product identity statements (e.g., "the game must be an RPG").
  If the brief states a high-level intention, translate it into concrete system-level capabilities when possible.
- Do NOT invent new features. Only derive what is directly implied and unavoidable.
- Do NOT duplicate requirements.
- If the brief is ambiguous (e.g., alternative decisions), capture it in "assumptions" instead of forcing a definitive requirement.
- Requirements must be atomic (one capability/constraint per requirement).
- Avoid vague words ("profundo", "escalable", "sorprendente", "inmersivo") unless grounded in a concrete capability.
- Generate between 12 and 18 requirements (minimum 12).
- Classify correctly:
  - "functional" = system behavior/capability.
  - "non_functional" = quality attribute, constraint, compliance, platform, performance, architectural concern.
- Respond ONLY with valid JSON using double quotes.
- Do NOT add extra fields outside the required schema.
- ALL text content MUST be written in Spanish.
- "actors" should include only relevant actors (e.g., Jugador, Diseñador de narrativa, Diseñador de niveles, Equipo de ingeniería, QA, Productor).
- priority must be exactly: "high", "medium", or "low" (DO NOT translate these)

REQUIRED JSON FORMAT (do not modify structure):

{
  "artifacts": [
    {
      "id": "REQ-001",
      "title": "Título corto en español",
      "description": "Descripcion detallada en espanol",
      "type": "functional",
      "priority": "medium",
      "actors": ["..."]
    }
  ],
  "domain_summary": "Resumen del dominio en español",
  "assumptions": ["Suposición o restricción del proyecto en español"]
}
"""


async def run_ba_agent(state: PipelineState) -> dict:
    """Read the brief and generate REQ-001, REQ-002... as structured JSON."""
    run_id = state["run_id"]
    brief = state.get("brief", "")

    await log_decision(run_id, "ba_agent", "started", {"brief_length": len(brief)})

    prompt = f"""
Analiza el siguiente brief y genera requisitos de ingeniería del sistema.
- Evita copiar frases del brief literalmente.
- Evita requisitos de identidad del producto (ej.: "el juego debe ser un RPG").
- Enfócate en capacidades técnicas y restricciones verificables del sistema.
- Si hay decisiones abiertas o ambigüedad, ponlas en "assumptions".

Brief:
{brief}

Responde SOLO con JSON.
"""

    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"\n\n## Feedback del revisor (aplícalo en tu respuesta)\n{feedback}"

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

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

