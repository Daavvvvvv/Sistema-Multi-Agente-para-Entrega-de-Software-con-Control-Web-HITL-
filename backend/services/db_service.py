"""Database operations for runs, artifacts, decision logs, and HITL gates."""

import json
import uuid

from database import get_db


# --- Runs ---

async def create_run(brief: str) -> dict:
    run_id = str(uuid.uuid4())[:8]
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO runs (id, brief, status, current_stage) VALUES (?, ?, 'created', 'pending')",
            (run_id, brief),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


async def list_runs() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM runs ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_run(run_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_run_status(run_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, status, current_stage FROM runs WHERE id = ?", (run_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def update_run_stage(run_id: str, status: str, stage: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE runs SET status = ?, current_stage = ?, updated_at = datetime('now') WHERE id = ?",
            (status, stage, run_id),
        )
        await db.commit()
    finally:
        await db.close()


# --- Artifacts ---

async def list_artifacts(run_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at", (run_id,)
        )
        rows = await cursor.fetchall()
        return [
            {**dict(r), "content": json.loads(r["content"]), "parent_ids": json.loads(r["parent_ids"])}
            for r in rows
        ]
    finally:
        await db.close()


async def get_artifact(run_id: str, artifact_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM artifacts WHERE run_id = ? AND id = ?",
            (run_id, artifact_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {**dict(row), "content": json.loads(row["content"]), "parent_ids": json.loads(row["parent_ids"])}
    finally:
        await db.close()


async def save_artifact(
    run_id: str, artifact_id: str, agent: str, artifact_type: str,
    content: dict, parent_ids: list[str] | None = None,
) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO artifacts (id, run_id, agent, type, content, parent_ids) VALUES (?, ?, ?, ?, ?, ?)",
            (artifact_id, run_id, agent, artifact_type, json.dumps(content), json.dumps(parent_ids or [])),
        )
        await db.commit()
    finally:
        await db.close()


async def get_diagram(run_id: str, diagram_type: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT content FROM artifacts WHERE run_id = ? AND type = ?",
            (run_id, f"diagram_{diagram_type}"),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return json.loads(row["content"])
    finally:
        await db.close()


# --- Decision Log ---

async def list_decision_logs(run_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM decision_log WHERE run_id = ? ORDER BY timestamp", (run_id,)
        )
        rows = await cursor.fetchall()
        return [
            {**dict(r), "details": json.loads(r["details"])}
            for r in rows
        ]
    finally:
        await db.close()


async def log_decision(run_id: str, agent: str, action: str, details: dict | None = None) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO decision_log (run_id, agent, action, details) VALUES (?, ?, ?, ?)",
            (run_id, agent, action, json.dumps(details or {})),
        )
        await db.commit()
    finally:
        await db.close()


# --- HITL Gates ---

async def get_pending_hitl(run_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM hitl_gates WHERE run_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
            (run_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def create_hitl_gate(run_id: str, stage: str) -> int:
    """Create a HITL gate and return its ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO hitl_gates (run_id, stage) VALUES (?, ?)",
            (run_id, stage),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_hitl_gate_by_id(gate_id: int) -> dict | None:
    """Get a specific HITL gate by its ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM hitl_gates WHERE id = ?", (gate_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def resolve_hitl(run_id: str, status: str, feedback: str | None) -> dict | None:
    """Resolve the current pending HITL gate. Returns {status, gate_id} or None if no pending gate."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM hitl_gates WHERE run_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
            (run_id,),
        )
        gate = await cursor.fetchone()
        if not gate:
            return None
        await db.execute(
            "UPDATE hitl_gates SET status = ?, feedback = ?, resolved_at = datetime('now') WHERE id = ?",
            (status, feedback, gate["id"]),
        )
        await db.commit()
        return {"status": status, "gate_id": gate["id"]}
    finally:
        await db.close()
