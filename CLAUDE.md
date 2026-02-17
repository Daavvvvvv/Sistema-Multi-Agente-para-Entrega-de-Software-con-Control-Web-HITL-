# CLAUDE.md — Contexto del Proyecto Multi-Agente SDLC

## Qué es este proyecto
Sistema multi-agente que transforma un brief de texto (.txt) en artefactos de ingeniería de software completos. Es un entregable académico para la materia "Procesos Modernos de Desarrollo" en Universidad EAFIT. Deadline: 7 días.

## Objetivo
Construir un pipeline donde mínimo 4-5 agentes de IA colaboran automáticamente (sin copiar/pegar manual entre ellos) para generar: requerimientos, inception/MVP, historias de usuario, casos de prueba, diagramas ER y de secuencia en SVG, y un log de decisiones. Todo controlado desde una interfaz web con puntos HITL (Human-in-the-Loop).

## Tech Stack
- **Backend/Orquestación**: Python + FastAPI + LangGraph
- **LLM**: Google Gemini (tier gratuito)
- **Persistencia**: SQLite
- **Frontend**: React + Vite
- **Diagramas**: Mermaid CLI → SVG
- **Comunicación**: REST API + polling (o SSE)

## Estructura del proyecto
```
multi-agent-sdlc/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── api/
│   │   ├── routes_runs.py       # Endpoints de ejecuciones
│   │   ├── routes_artifacts.py  # Endpoints de artefactos
│   │   ├── routes_hitl.py       # Endpoints HITL
│   │   └── routes_logs.py       # Endpoints de logs
│   ├── agents/
│   │   ├── graph.py             # Grafo LangGraph
│   │   ├── state.py             # Estado compartido del pipeline
│   │   ├── ba_agent.py          # Agente de Requerimientos (BA)
│   │   ├── product_agent.py     # Agente Product/Inception/MVP
│   │   ├── analyst_agent.py     # Agente Historias de Usuario
│   │   ├── qa_agent.py          # Agente QA/Test Cases
│   │   └── design_agent.py      # Agente Diseño (ER + Secuencia)
│   ├── services/
│   │   ├── llm_service.py       # Wrapper Gemini API
│   │   ├── diagram_service.py   # Mermaid → SVG
│   │   └── db_service.py        # Operaciones SQLite
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   ├── database.py              # Conexión SQLite + creación tablas
│   ├── requirements.txt
│   └── data/runs/               # Archivos generados por run
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx          # Lista de runs + nueva ejecución
│   │   │   └── RunDetail.jsx     # Detalle de un run
│   │   ├── components/
│   │   │   ├── BriefUpload.jsx   # Upload .txt o textarea
│   │   │   ├── PipelineStatus.jsx
│   │   │   ├── ArtifactViewer.jsx
│   │   │   ├── HitlControls.jsx
│   │   │   ├── DecisionLog.jsx
│   │   │   └── DiagramViewer.jsx
│   │   └── services/
│   │       └── api.js
│   ├── package.json
│   └── vite.config.js
├── CLAUDE.md
└── README.md
```

## Pipeline de Agentes (flujo)
```
Brief .txt → Agente BA → HITL #1 → Agente Product → HITL #2 → Agente Analyst → HITL #3 → Agente QA → Agente Design → HITL #4 → Done
```
- Si HITL rechaza → re-ejecuta agente anterior con feedback
- Si HITL pide cambios → agente regenera con feedback adicional
- Sin intervención humana ENTRE agentes, solo en gates HITL

## 5 Agentes
1. **BA Agent** (Requerimientos): Lee brief → genera REQ-001, REQ-002... como JSON
2. **Product Agent** (Inception/MVP): Recibe REQs → genera INC-001 con scope MVP, riesgos, priorización
3. **Analyst Agent** (Historias): Recibe REQs + INC → genera US-001, US-002... con criterios de aceptación
4. **QA Agent** (Test Cases): Recibe US → genera TC-001, TC-002... vinculados a user stories
5. **Design Agent** (Diagramas): Recibe todo → genera diagrama ER y secuencia en Mermaid → SVG

## 7 Artefactos obligatorios
1. Requerimientos (REQ-xxx) — JSON
2. Inception/MVP (INC-xxx) — JSON
3. Historias + criterios de aceptación (US-xxx) — JSON
4. Casos de prueba (TC-xxx) — JSON
5. Diagrama ER — SVG (via Mermaid)
6. Diagrama de secuencia — SVG (via Mermaid)
7. Log de decisiones — JSON estructurado (agente, timestamp, acción, justificación, artefactos)

## Trazabilidad obligatoria
Cada artefacto referencia a sus padres con IDs:
REQ-001 → US-001 (requirement_ids: ["REQ-001"]) → TC-001 (user_story_ids: ["US-001"])
Los diagramas referencian REQs y USs.

## Schemas JSON de artefactos

### Requerimientos (BA output)
```json
{
  "artifacts": [
    { "id": "REQ-001", "title": "...", "description": "...", "type": "functional|non_functional", "priority": "high|medium|low", "actors": ["..."] }
  ],
  "domain_summary": "...",
  "assumptions": ["..."]
}
```

### Inception/MVP (Product output)
```json
{
  "id": "INC-001",
  "mvp_scope": { "included_reqs": ["REQ-001"], "excluded_reqs": ["REQ-005"], "justification": "..." },
  "risks": [{ "id": "RISK-001", "description": "...", "impact": "high", "mitigation": "..." }],
  "success_criteria": ["..."]
}
```

### Historias de Usuario (Analyst output)
```json
{
  "artifacts": [
    { "id": "US-001", "title": "...", "requirement_ids": ["REQ-001"], "story": "Como..., quiero..., para...", "acceptance_criteria": ["DADO...CUANDO...ENTONCES..."], "priority": "high", "estimation": "3 SP" }
  ]
}
```

### Casos de Prueba (QA output)
```json
{
  "artifacts": [
    { "id": "TC-001", "title": "...", "user_story_ids": ["US-001"], "requirement_ids": ["REQ-001"], "preconditions": ["..."], "steps": ["..."], "expected_result": "...", "type": "positive|negative" }
  ]
}
```

### Diagramas (Design output)
```json
{
  "er_diagram": { "mermaid_code": "erDiagram\n...", "referenced_reqs": ["REQ-001"], "description": "..." },
  "sequence_diagram": { "mermaid_code": "sequenceDiagram\n...", "referenced_stories": ["US-001"], "description": "..." }
}
```

## SQLite Tables
- `runs` (id, brief, status, current_stage, timestamps)
- `artifacts` (id like REQ-001, run_id, agent, type, content JSON, parent_ids JSON array)
- `decision_log` (run_id, agent, action, details JSON, timestamp)
- `hitl_gates` (run_id, stage, status, feedback, timestamps)

## API Endpoints
- POST /api/runs — crear run con brief
- GET /api/runs/{id} — detalle del run
- GET /api/runs/{id}/status — estado para polling
- GET /api/runs/{id}/artifacts — todos los artefactos
- GET /api/runs/{id}/artifacts/{art_id} — artefacto específico
- GET /api/runs/{id}/hitl/current — gate HITL pendiente
- POST /api/runs/{id}/hitl/approve — aprobar
- POST /api/runs/{id}/hitl/reject — rechazar
- POST /api/runs/{id}/hitl/request-changes — pedir cambios con feedback
- GET /api/runs/{id}/logs — log de decisiones
- GET /api/runs/{id}/diagrams/er — SVG ER
- GET /api/runs/{id}/diagrams/sequence — SVG secuencia

## LangGraph State
```python
class PipelineState(TypedDict):
    run_id: str
    brief: str
    current_stage: str
    requirements: Optional[dict]
    inception: Optional[dict]
    user_stories: Optional[dict]
    test_cases: Optional[dict]
    diagrams: Optional[dict]
    hitl_status: Optional[str]    # pending | approved | rejected | changes
    hitl_feedback: Optional[str]
    error: Optional[str]
    retry_count: int
```

## Rúbrica (100 pts)
- (20) Demo web y operabilidad
- (25) Flujo multi-agente real sin pasamanos
- (20) Calidad y consistencia de artefactos
- (15) Trazabilidad auditable
- (15) Log de decisiones y transparencia
- (5) Ingeniería del sistema (repo, README)
- (+5 bonus) Pruebas ejecutables
- (+5 bonus) Deploy

## Restricción clave
PROHIBIDO copiar/pegar manualmente outputs entre agentes. El flujo debe ser automático. Solo HITL permitido para aprobar/rechazar/solicitar cambios desde la web.

## Convenciones
- Python backend con type hints y Pydantic models
- React frontend con componentes funcionales y hooks
- Todos los agentes reciben y producen JSON estructurado
- Los prompts deben pedir explícitamente JSON válido como respuesta
- Manejar errores de parsing JSON del LLM con reintentos