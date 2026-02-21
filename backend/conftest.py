"""Shared fixtures for pytest — test DB, test client, fake artifact data."""

import os
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

# Use a separate test database so we don't pollute the real one
os.environ.setdefault("TESTING", "1")

import database  # noqa: E402

# Override DB path BEFORE any import that touches it
database.DB_PATH = "data/test_sdlc.db"

from main import app  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
from database import init_db, get_db  # noqa: E402
from services import db_service  # noqa: E402


# ---------- event loop ----------

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------- fresh database per test ----------

@pytest_asyncio.fixture(autouse=True)
async def fresh_db():
    """Create tables before each test and drop them after."""
    await init_db()
    yield
    # Clean up
    db = await get_db()
    try:
        await db.executescript(
            "DELETE FROM hitl_gates; DELETE FROM decision_log; DELETE FROM artifacts; DELETE FROM runs;"
        )
        await db.commit()
    finally:
        await db.close()


# ---------- mock pipeline (don't call the LLM during tests) ----------

@pytest.fixture(autouse=True)
def mock_pipeline():
    """Prevent POST /api/runs from triggering the real pipeline (which calls the LLM)."""
    with patch("api.routes_runs.run_pipeline", new_callable=AsyncMock):
        yield


# ---------- async HTTP client ----------

@pytest_asyncio.fixture
async def client():
    """AsyncClient that talks to the FastAPI app without starting a server."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------- fake data from each agent ----------

FAKE_REQUIREMENTS = {
    "artifacts": [
        {
            "id": "REQ-001",
            "title": "Registro de usuarios",
            "description": "Los usuarios deben poder registrarse con email y contraseña",
            "type": "functional",
            "priority": "high",
            "actors": ["Jugador"],
        },
        {
            "id": "REQ-002",
            "title": "Catálogo de productos",
            "description": "El sistema debe mostrar una lista de productos disponibles",
            "type": "functional",
            "priority": "high",
            "actors": ["Jugador", "Administrador"],
        },
        {
            "id": "REQ-003",
            "title": "Rendimiento del sistema",
            "description": "El sistema debe soportar al menos 100 usuarios concurrentes",
            "type": "non_functional",
            "priority": "medium",
            "actors": [],
        },
    ],
    "domain_summary": "Plataforma de comercio electrónico",
    "assumptions": ["Los usuarios tienen acceso a internet"],
}

FAKE_INCEPTION = {
    "id": "INC-001",
    "title": "Inception del MVP",
    "requirement_ids": ["REQ-001", "REQ-002", "REQ-003"],
    "mvp_scope": {
        "included_reqs": ["REQ-001", "REQ-002"],
        "excluded_reqs": ["REQ-003"],
        "justification": "Los requisitos funcionales son esenciales para el MVP",
    },
    "risks": [
        {
            "id": "RISK-001",
            "description": "Tiempo de desarrollo insuficiente",
            "impact": "high",
            "mitigation": "Priorizar funcionalidades críticas",
        }
    ],
    "success_criteria": [
        "Los usuarios pueden registrarse exitosamente",
        "El catálogo de productos se muestra correctamente",
    ],
}

FAKE_USER_STORIES = {
    "artifacts": [
        {
            "id": "US-001",
            "title": "Registro de usuario",
            "requirement_ids": ["REQ-001"],
            "story": "Como jugador, quiero registrarme con email y contraseña, para acceder a la plataforma",
            "acceptance_criteria": [
                "Escenario 1 (positivo): DADO que estoy en la página de registro CUANDO ingreso datos válidos ENTONCES se crea mi cuenta",
                "Escenario 2 (negativo): DADO que estoy en la página de registro CUANDO ingreso un email ya registrado ENTONCES veo un mensaje de error",
            ],
            "priority": "high",
            "estimation": "M",
        },
        {
            "id": "US-002",
            "title": "Ver catálogo",
            "requirement_ids": ["REQ-002"],
            "story": "Como jugador, quiero ver el catálogo de productos, para elegir qué comprar",
            "acceptance_criteria": [
                "Escenario 1 (positivo): DADO que estoy logueado CUANDO accedo al catálogo ENTONCES veo productos con precios",
            ],
            "priority": "high",
            "estimation": "L",
        },
    ]
}

FAKE_TEST_CASES = {
    "artifacts": [
        {
            "id": "TC-001",
            "title": "Registro exitoso",
            "user_story_ids": ["US-001"],
            "requirement_ids": ["REQ-001"],
            "preconditions": ["El usuario no tiene cuenta previa"],
            "steps": [
                "DADO que estoy en la página de registro",
                "CUANDO ingreso email y contraseña válidos",
                "ENTONCES se crea mi cuenta",
            ],
            "expected_result": "La cuenta se crea y se redirige al inicio",
            "type": "positive",
        },
        {
            "id": "TC-002",
            "title": "Registro con email duplicado",
            "user_story_ids": ["US-001"],
            "requirement_ids": ["REQ-001"],
            "preconditions": ["Ya existe una cuenta con el email"],
            "steps": [
                "DADO que estoy en la página de registro",
                "CUANDO ingreso un email ya registrado",
                "ENTONCES veo un mensaje de error",
            ],
            "expected_result": "Se muestra error 'Email ya registrado'",
            "type": "negative",
        },
    ]
}

FAKE_DIAGRAMS = {
    "er_diagram": {
        "mermaid_code": "erDiagram\n    USUARIO ||--o{ PEDIDO : realiza\n    PEDIDO ||--|{ PRODUCTO : contiene",
        "referenced_reqs": ["REQ-001", "REQ-002"],
        "referenced_stories": [],
        "description": "Diagrama ER del dominio de comercio electrónico",
    },
    "sequence_diagram": {
        "mermaid_code": "sequenceDiagram\n    actor U as Usuario\n    U->>Sistema: Registrarse\n    Sistema-->>U: Confirmación",
        "referenced_reqs": [],
        "referenced_stories": ["US-001"],
        "description": "Diagrama de secuencia del flujo de registro",
    },
}
