"""Tests for db_service — CRUD operations on runs, artifacts, logs, HITL gates."""

import json
import pytest

from services import db_service


# ─── Runs ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_run():
    run = await db_service.create_run("Brief de prueba")
    assert run["id"]
    assert run["brief"] == "Brief de prueba"
    assert run["status"] == "created"
    assert run["current_stage"] == "pending"

    fetched = await db_service.get_run(run["id"])
    assert fetched is not None
    assert fetched["id"] == run["id"]


@pytest.mark.asyncio
async def test_list_runs():
    await db_service.create_run("Brief A")
    await db_service.create_run("Brief B")
    runs = await db_service.list_runs()
    assert len(runs) >= 2


@pytest.mark.asyncio
async def test_get_run_not_found():
    result = await db_service.get_run("does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_update_run_stage():
    run = await db_service.create_run("Brief")
    await db_service.update_run_stage(run["id"], "running", "ba")

    updated = await db_service.get_run(run["id"])
    assert updated["status"] == "running"
    assert updated["current_stage"] == "ba"


@pytest.mark.asyncio
async def test_get_run_status():
    run = await db_service.create_run("Brief")
    status = await db_service.get_run_status(run["id"])
    assert status["id"] == run["id"]
    assert status["status"] == "created"
    assert status["current_stage"] == "pending"


# ─── Artifacts ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_and_list_artifacts():
    run = await db_service.create_run("Brief")

    await db_service.save_artifact(
        run_id=run["id"],
        artifact_id="REQ-001",
        agent="ba_agent",
        artifact_type="requirement",
        content={"id": "REQ-001", "title": "Test"},
        parent_ids=[],
    )
    await db_service.save_artifact(
        run_id=run["id"],
        artifact_id="REQ-002",
        agent="ba_agent",
        artifact_type="requirement",
        content={"id": "REQ-002", "title": "Test 2"},
        parent_ids=[],
    )

    artifacts = await db_service.list_artifacts(run["id"])
    assert len(artifacts) == 2
    assert artifacts[0]["id"] == "REQ-001"
    assert artifacts[0]["content"]["title"] == "Test"


@pytest.mark.asyncio
async def test_get_artifact():
    run = await db_service.create_run("Brief")

    await db_service.save_artifact(
        run_id=run["id"],
        artifact_id="US-001",
        agent="analyst_agent",
        artifact_type="user_story",
        content={"id": "US-001", "story": "Como usuario..."},
        parent_ids=["REQ-001"],
    )

    art = await db_service.get_artifact(run["id"], "US-001")
    assert art is not None
    assert art["content"]["story"] == "Como usuario..."
    assert art["parent_ids"] == ["REQ-001"]


@pytest.mark.asyncio
async def test_get_artifact_not_found():
    run = await db_service.create_run("Brief")
    assert await db_service.get_artifact(run["id"], "NOPE") is None


@pytest.mark.asyncio
async def test_save_artifact_upsert():
    """INSERT OR REPLACE should update an existing artifact."""
    run = await db_service.create_run("Brief")

    await db_service.save_artifact(
        run_id=run["id"],
        artifact_id="REQ-001",
        agent="ba_agent",
        artifact_type="requirement",
        content={"id": "REQ-001", "title": "Version 1"},
        parent_ids=[],
    )
    await db_service.save_artifact(
        run_id=run["id"],
        artifact_id="REQ-001",
        agent="ba_agent",
        artifact_type="requirement",
        content={"id": "REQ-001", "title": "Version 2"},
        parent_ids=[],
    )

    art = await db_service.get_artifact(run["id"], "REQ-001")
    assert art["content"]["title"] == "Version 2"

    # Should still be only 1 artifact, not 2
    all_arts = await db_service.list_artifacts(run["id"])
    assert len(all_arts) == 1


@pytest.mark.asyncio
async def test_get_diagram():
    run = await db_service.create_run("Brief")

    await db_service.save_artifact(
        run_id=run["id"],
        artifact_id="DIAG-ER",
        agent="design_agent",
        artifact_type="diagram_er",
        content={"mermaid_code": "erDiagram\n  A ||--o{ B : has"},
        parent_ids=[],
    )

    diagram = await db_service.get_diagram(run["id"], "er")
    assert diagram is not None
    assert "mermaid_code" in diagram
    assert diagram["mermaid_code"].startswith("erDiagram")


@pytest.mark.asyncio
async def test_get_diagram_not_found():
    run = await db_service.create_run("Brief")
    assert await db_service.get_diagram(run["id"], "er") is None


# ─── Decision Log ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_and_list_decisions():
    run = await db_service.create_run("Brief")

    await db_service.log_decision(run["id"], "ba_agent", "started", {"brief_length": 100})
    await db_service.log_decision(run["id"], "ba_agent", "completed", {"reqs": 5})

    logs = await db_service.list_decision_logs(run["id"])
    assert len(logs) == 2
    assert logs[0]["agent"] == "ba_agent"
    assert logs[0]["action"] == "started"
    assert logs[0]["details"]["brief_length"] == 100
    assert logs[1]["action"] == "completed"
    assert "timestamp" in logs[0]


# ─── HITL Gates ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_hitl_gate():
    run = await db_service.create_run("Brief")
    gate_id = await db_service.create_hitl_gate(run["id"], "ba")

    gate = await db_service.get_hitl_gate_by_id(gate_id)
    assert gate is not None
    assert gate["stage"] == "ba"
    assert gate["status"] == "pending"
    assert gate["feedback"] is None


@pytest.mark.asyncio
async def test_get_pending_hitl():
    run = await db_service.create_run("Brief")
    await db_service.create_hitl_gate(run["id"], "product")

    pending = await db_service.get_pending_hitl(run["id"])
    assert pending is not None
    assert pending["stage"] == "product"
    assert pending["status"] == "pending"


@pytest.mark.asyncio
async def test_get_pending_hitl_none():
    run = await db_service.create_run("Brief")
    assert await db_service.get_pending_hitl(run["id"]) is None


@pytest.mark.asyncio
async def test_resolve_hitl_approve():
    run = await db_service.create_run("Brief")
    await db_service.create_hitl_gate(run["id"], "ba")

    result = await db_service.resolve_hitl(run["id"], "approved", None)
    assert result is not None
    assert result["status"] == "approved"

    # No more pending
    assert await db_service.get_pending_hitl(run["id"]) is None


@pytest.mark.asyncio
async def test_resolve_hitl_with_feedback():
    run = await db_service.create_run("Brief")
    gate_id = await db_service.create_hitl_gate(run["id"], "analyst")

    result = await db_service.resolve_hitl(run["id"], "changes", "Necesita más detalle")
    assert result["status"] == "changes"

    # Verify feedback was saved
    gate = await db_service.get_hitl_gate_by_id(gate_id)
    assert gate["feedback"] == "Necesita más detalle"
    assert gate["status"] == "changes"
    assert gate["resolved_at"] is not None


@pytest.mark.asyncio
async def test_resolve_hitl_no_pending():
    run = await db_service.create_run("Brief")
    result = await db_service.resolve_hitl(run["id"], "approved", None)
    assert result is None
