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

## Comandos utiles

| Comando | Descripcion |
|---------|------------|
| `python main.py` | Iniciar backend (desde `backend/` con venv activado) |
| `pnpm dev` | Iniciar frontend en modo desarrollo (desde `frontend/`) |
| `pnpm build` | Build de produccion del frontend |
| `http://localhost:8000/docs` | Swagger UI para probar la API |
