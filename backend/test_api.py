"""Tests for FastAPI endpoints — runs, artifacts, HITL, logs."""

import pytest
from httpx import AsyncClient

from services import db_service


# ─── Runs ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_create_run(client: AsyncClient):
    r = await client.post("/api/runs", json={"brief": "Test brief for e-commerce"})
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["brief"] == "Test brief for e-commerce"
    assert data["status"] == "created"
    assert data["current_stage"] == "pending"


@pytest.mark.asyncio
async def test_create_run_empty_brief(client: AsyncClient):
    """Even empty brief should create a run (validation is business logic)."""
    r = await client.post("/api/runs", json={"brief": ""})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_list_runs(client: AsyncClient):
    await client.post("/api/runs", json={"brief": "Brief 1"})
    await client.post("/api/runs", json={"brief": "Brief 2"})
    r = await client.get("/api/runs")
    assert r.status_code == 200
    runs = r.json()
    assert len(runs) >= 2


@pytest.mark.asyncio
async def test_get_run(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test brief"})
    run_id = create.json()["id"]

    r = await client.get(f"/api/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["id"] == run_id


@pytest.mark.asyncio
async def test_get_run_not_found(client: AsyncClient):
    r = await client.get("/api/runs/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_run_status(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test brief"})
    run_id = create.json()["id"]

    r = await client.get(f"/api/runs/{run_id}/status")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == run_id
    assert data["status"] == "created"
    assert data["current_stage"] == "pending"


# ─── Artifacts ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_artifacts_empty(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    r = await client.get(f"/api/runs/{run_id}/artifacts")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_artifacts_with_data(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    # Save a requirement artifact directly via db_service
    await db_service.save_artifact(
        run_id=run_id,
        artifact_id="REQ-001",
        agent="ba_agent",
        artifact_type="requirement",
        content={"id": "REQ-001", "title": "Test req", "type": "functional"},
        parent_ids=[],
    )

    r = await client.get(f"/api/runs/{run_id}/artifacts")
    assert r.status_code == 200
    artifacts = r.json()
    assert len(artifacts) == 1
    assert artifacts[0]["id"] == "REQ-001"
    assert artifacts[0]["agent"] == "ba_agent"
    assert artifacts[0]["content"]["title"] == "Test req"


@pytest.mark.asyncio
async def test_get_single_artifact(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    await db_service.save_artifact(
        run_id=run_id,
        artifact_id="US-001",
        agent="analyst_agent",
        artifact_type="user_story",
        content={"id": "US-001", "title": "Test story", "story": "Como usuario..."},
        parent_ids=["REQ-001"],
    )

    r = await client.get(f"/api/runs/{run_id}/artifacts/US-001")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "US-001"
    assert data["parent_ids"] == ["REQ-001"]


@pytest.mark.asyncio
async def test_get_artifact_not_found(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    r = await client.get(f"/api/runs/{run_id}/artifacts/NOPE")
    assert r.status_code == 404


# ─── Diagrams ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_diagram(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    await db_service.save_artifact(
        run_id=run_id,
        artifact_id="DIAG-ER",
        agent="design_agent",
        artifact_type="diagram_er",
        content={"mermaid_code": "erDiagram\n  A ||--o{ B : has", "description": "Test ER"},
        parent_ids=["REQ-001"],
    )

    r = await client.get(f"/api/runs/{run_id}/diagrams/er")
    assert r.status_code == 200
    data = r.json()
    assert "mermaid_code" in data
    assert data["mermaid_code"].startswith("erDiagram")


@pytest.mark.asyncio
async def test_get_diagram_invalid_type(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    r = await client.get(f"/api/runs/{run_id}/diagrams/invalid")
    assert r.status_code == 400


# ─── HITL ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hitl_flow(client: AsyncClient):
    """Full HITL cycle: create gate → get pending → approve."""
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    # No pending gate initially
    r = await client.get(f"/api/runs/{run_id}/hitl/current")
    assert r.status_code == 200
    assert r.json() is None

    # Create a gate manually via db_service
    gate_id = await db_service.create_hitl_gate(run_id, "ba")

    # Now there should be a pending gate
    r = await client.get(f"/api/runs/{run_id}/hitl/current")
    assert r.status_code == 200
    gate = r.json()
    assert gate["stage"] == "ba"
    assert gate["status"] == "pending"

    # Approve it
    r = await client.post(f"/api/runs/{run_id}/hitl/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # No more pending gates
    r = await client.get(f"/api/runs/{run_id}/hitl/current")
    assert r.json() is None


@pytest.mark.asyncio
async def test_hitl_reject(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    await db_service.create_hitl_gate(run_id, "product")

    r = await client.post(f"/api/runs/{run_id}/hitl/reject")
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_hitl_request_changes(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    await db_service.create_hitl_gate(run_id, "analyst")

    r = await client.post(
        f"/api/runs/{run_id}/hitl/request-changes",
        json={"feedback": "Agregar más criterios de aceptación por favor"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "changes"


@pytest.mark.asyncio
async def test_hitl_approve_no_gate(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    r = await client.post(f"/api/runs/{run_id}/hitl/approve")
    assert r.status_code == 404


# ─── Decision Logs ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decision_logs(client: AsyncClient):
    create = await client.post("/api/runs", json={"brief": "Test"})
    run_id = create.json()["id"]

    await db_service.log_decision(run_id, "ba_agent", "started", {"brief_length": 42})
    await db_service.log_decision(run_id, "ba_agent", "completed", {"requirements_generated": 5})

    r = await client.get(f"/api/runs/{run_id}/logs")
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) == 2
    assert logs[0]["agent"] == "ba_agent"
    assert logs[0]["action"] == "started"
    assert logs[1]["action"] == "completed"
    assert "timestamp" in logs[0]
