"""BA Agent — Requirements extraction from brief."""

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """
Eres un analista de requisitos de software.

Extrae los requisitos explícitos del texto proporcionado.

Reglas:
- No infieras información.
- No agregues texto adicional.
- Devuelve únicamente JSON válido.
- Usa comillas dobles.
- El campo "type" debe ser:
  - "functional" o
  - "non_functional"
- El campo "priority" debe ser:
  - "high", "medium" o "low"
- Genera un id único corto para cada requisito (por ejemplo: REQ-001).

Formato obligatorio:

{
  "artifacts": [
    {
      "id": "REQ-001",
      "title": "Título corto",
      "description": "Descripción detallada",
      "type": "functional",
      "priority": "medium",
      "actors": []
    }
  ],
  "domain_summary": "",
  "assumptions": []
}
"""

async def run_ba_agent(state: PipelineState) -> dict:
    """Read the brief and generate REQ-001, REQ-002... as structured JSON."""
    # TODO: implement with LLM call
    run_id=state["run_id"]
    brief = state.get("brief","")
    prompt = f"""
                    Analiza el siguiente brief y extrae los requisitos:
                    {brief}
                    Responde SOLO con JSON.
              """
    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # 5️⃣ Guardar artefactos en DB
    for item in result.get("artifacts", []):
        await save_artifact(
            run_id=run_id,
            artifact_id=item["id"],
            agent="ba_agent",
            artifact_type="requirement",
            content=item,
            parent_ids=[]
        )          
    await log_decision(run_id, "ba_agent", "started", {"brief_length": len(brief)})
    return {"requirements": result}
    
