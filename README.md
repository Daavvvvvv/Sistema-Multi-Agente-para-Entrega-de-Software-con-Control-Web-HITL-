# Sistema Multi-Agente para Entrega de Software con Control Web HITL

Sistema multi-agente que transforma un brief de texto en artefactos de ingenieria de software completos, controlado desde una interfaz web con puntos HITL (Human-in-the-Loop).

**Materia:** Procesos Modernos de Desarrollo — Universidad EAFIT

## Requisitos previos

- **Python** 3.12+
- **Node.js** 22+ (LTS)
- **pnpm** (`npm install -g pnpm`)

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/Daavvvvvv/Sistema-Multi-Agente-para-Entrega-de-Software-con-Control-Web-HITL-.git
cd Sistema-Multi-Agente-para-Entrega-de-Software-con-Control-Web-HITL-
```

### 2. Backend

```bash
cd backend
python -m venv .venv
```

Activar el entorno virtual:

- **Windows (Git Bash / MINGW):**
  ```bash
  source .venv/Scripts/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Mac / Linux:**
  ```bash
  source .venv/bin/activate
  ```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Crear el archivo `.env` (copiar del ejemplo):

```bash
cp .env.example .env
```

Editar `.env` y configurar el proveedor de LLM. El servicio es compatible con cualquier API OpenAI-compatible:

```
LLM_API_KEY=tu_api_key_aqui
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
```

Proveedores soportados:

| Proveedor | Base URL | Modelo sugerido |
|-----------|----------|----------------|
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Google Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` |
| OpenRouter | `https://openrouter.ai/api/v1` | `qwen/qwen-2.5-72b-instruct` |

### 3. Frontend

```bash
cd frontend
pnpm install
```

## Ejecucion

Necesitas **dos terminales**:

### Terminal 1 — Backend (desde `backend/`)

```bash
source .venv/Scripts/activate
python main.py
```

El servidor FastAPI arranca en `http://localhost:8000`

### Terminal 2 — Frontend (desde `frontend/`)

```bash
pnpm dev
```

Vite arranca en `http://localhost:5173`

### Verificar

1. Abrir `http://localhost:5173` en el navegador
2. Debe aparecer el mensaje verde **"Backend connected"** con la hora del servidor
3. La API esta disponible en `http://localhost:8000/docs` (Swagger UI)

## Tech Stack

| Capa | Tecnologia |
|------|-----------|
| Backend | Python + FastAPI + LangGraph |
| LLM | Cualquier API OpenAI-compatible (Groq, DeepSeek, Gemini, Qwen) |
| Base de datos | SQLite |
| Frontend | React + Vite + TypeScript |
| Diagramas | Mermaid CLI → SVG |

## Estructura del proyecto

```
├── backend/
│   ├── main.py              # FastAPI app
│   ├── database.py          # Conexion SQLite + tablas
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/                 # Endpoints (thin routes)
│   ├── agents/              # LangGraph pipeline + agentes
│   ├── services/            # Logica de negocio (DB, LLM, diagramas)
│   └── models/              # Pydantic schemas
├── frontend/
│   ├── src/
│   │   ├── pages/           # Home, RunDetail
│   │   ├── components/      # BriefUpload, PipelineStatus, etc.
│   │   └── services/        # API client (axios)
│   ├── vite.config.ts
│   └── package.json
└── README.md
```

## Guia para implementar agentes

Cada agente sigue el mismo patron. Mira `backend/agents/qa_agent.py` o `design_agent.py` como referencia.

### Patron base

```python
"""Mi Agent — Descripcion."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """Tu eres un agente de [rol]..."""

USER_PROMPT_TEMPLATE = """...\n{variable}\n...\nResponde SOLO con JSON."""


async def run_mi_agent(state: PipelineState) -> dict:
    run_id = state["run_id"]

    # 1. Leer datos de entrada del state
    datos = state.get("campo_anterior") or {}

    # 2. Log de inicio
    await log_decision(run_id, "mi_agent", "started", {"info": "..."})

    # 3. Construir prompt
    prompt = USER_PROMPT_TEMPLATE.format(variable=json.dumps(datos, indent=2, ensure_ascii=False))

    # 4. Si hay feedback de HITL, agregarlo al prompt
    feedback = state.get("hitl_feedback")
    if feedback:
        prompt += f"\n\n## HITL Feedback\n{feedback}"

    # 5. Llamar al LLM (retorna dict parseado)
    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # 6. Guardar artefactos en la DB
    for item in result.get("artifacts", []):
        await save_artifact(
            run_id=run_id,
            artifact_id=item["id"],
            agent="mi_agent",
            artifact_type="tipo",
            content=item,
            parent_ids=item.get("parent_field", []),
        )

    # 7. Log de fin
    await log_decision(run_id, "mi_agent", "completed", {"count": len(result.get("artifacts", []))})

    # 8. Retornar actualizacion del state (la key DEBE coincidir con PipelineState)
    return {"campo_state": result}
```

### Agentes pendientes

| Agente | Archivo | Lee del state | Escribe en state | Artefactos |
|--------|---------|---------------|------------------|------------|
| **BA** | `ba_agent.py` | `state["brief"]` | `return {"requirements": result}` | REQ-001, REQ-002... |
| **Product** | `product_agent.py` | `state["requirements"]` | `return {"inception": result}` | INC-001 |
| **Analyst** | `analyst_agent.py` | `state["requirements"]`, `state["inception"]` | `return {"user_stories": result}` | US-001, US-002... |

### Schemas JSON esperados

Cada agente debe retornar JSON que siga los schemas definidos en `CLAUDE.md` (seccion "Schemas JSON de artefactos").

### Servicios disponibles

| Funcion | Import | Que hace |
|---------|--------|----------|
| `call_llm_json(prompt, system)` | `from services.llm_service import call_llm_json` | Llama al LLM y parsea JSON (con reintento) |
| `call_llm(prompt, system)` | `from services.llm_service import call_llm` | Llama al LLM y retorna texto raw |
| `save_artifact(run_id, id, agent, type, content, parent_ids)` | `from services.db_service import save_artifact` | Guarda un artefacto en la DB |
| `log_decision(run_id, agent, action, details)` | `from services.db_service import log_decision` | Registra una decision en el log |

### Pipeline flow

```
Brief → BA Agent → HITL #1 → Product Agent → HITL #2 → Analyst Agent → HITL #3 → QA Agent → Design Agent → HITL #4 → Done
```

El pipeline (`graph.py`) ya esta construido. Solo implementen la funcion `run_xxx_agent(state)` en su archivo y todo funciona automaticamente.

## Comandos utiles

| Comando | Descripcion |
|---------|------------|
| `python main.py` | Iniciar backend (desde `backend/` con venv activado) |
| `pnpm dev` | Iniciar frontend en modo desarrollo (desde `frontend/`) |
| `pnpm build` | Build de produccion del frontend |
| `http://localhost:8000/docs` | Swagger UI para probar la API |
