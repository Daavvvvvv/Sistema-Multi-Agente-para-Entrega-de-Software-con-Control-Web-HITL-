"""LangGraph pipeline — wires all agents + HITL gates."""

import asyncio

from langgraph.graph import START, END, StateGraph

from agents.state import PipelineState
from agents.ba_agent import run_ba_agent
from agents.product_agent import run_product_agent
from agents.analyst_agent import run_analyst_agent
from agents.qa_agent import run_qa_agent
from agents.design_agent import run_design_agent
from services.db_service import (
    create_hitl_gate,
    get_hitl_gate_by_id,
    update_run_stage,
    log_decision,
)

HITL_POLL_INTERVAL = 2  # seconds


# ---------------------------------------------------------------------------
# Helper: poll a HITL gate until resolved
# ---------------------------------------------------------------------------
async def _poll_hitl(gate_id: int) -> dict:
    """Block until a HITL gate is resolved, then return it."""
    while True:
        gate = await get_hitl_gate_by_id(gate_id)
        if gate and gate["status"] != "pending":
            return gate
        await asyncio.sleep(HITL_POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Generic HITL node
# ---------------------------------------------------------------------------
async def _hitl_node(state: PipelineState, stage: str) -> dict:
    """Create a HITL gate, wait for resolution, return result."""
    run_id = state["run_id"]
    gate_id = await create_hitl_gate(run_id, stage)
    await update_run_stage(run_id, "waiting_hitl", f"hitl_{stage}")
    await log_decision(run_id, "pipeline", "hitl_gate_created", {"stage": stage})

    resolution = await _poll_hitl(gate_id)

    await log_decision(run_id, "pipeline", "hitl_resolved", {
        "stage": stage,
        "status": resolution["status"],
        "feedback": resolution.get("feedback"),
    })

    return {
        "hitl_status": resolution["status"],
        "hitl_feedback": resolution.get("feedback"),
    }


# ---------------------------------------------------------------------------
# Agent nodes
# ---------------------------------------------------------------------------
async def ba_node(state: PipelineState) -> dict:
    await update_run_stage(state["run_id"], "running", "ba")
    result = await run_ba_agent(state)
    return {"requirements": result["requirements"], "current_stage": "ba",
            "hitl_status": None, "hitl_feedback": None}


async def product_node(state: PipelineState) -> dict:
    await update_run_stage(state["run_id"], "running", "product")
    result = await run_product_agent(state)
    return {"inception": result["inception"], "current_stage": "product",
            "hitl_status": None, "hitl_feedback": None}


async def analyst_node(state: PipelineState) -> dict:
    await update_run_stage(state["run_id"], "running", "analyst")
    result = await run_analyst_agent(state)
    return {"user_stories": result["user_stories"], "current_stage": "analyst",
            "hitl_status": None, "hitl_feedback": None}


async def qa_node(state: PipelineState) -> dict:
    await update_run_stage(state["run_id"], "running", "qa")
    result = await run_qa_agent(state)
    return {"test_cases": result["test_cases"], "current_stage": "qa",
            "hitl_status": None, "hitl_feedback": None}


async def design_node(state: PipelineState) -> dict:
    await update_run_stage(state["run_id"], "running", "design")
    result = await run_design_agent(state)
    return {"diagrams": result["diagrams"], "current_stage": "design",
            "hitl_status": None, "hitl_feedback": None}


async def done_node(state: PipelineState) -> dict:
    await update_run_stage(state["run_id"], "completed", "done")
    await log_decision(state["run_id"], "pipeline", "pipeline_completed", {})
    return {"current_stage": "done"}


async def rejected_node(state: PipelineState) -> dict:
    """Pipeline stopped by HITL rejection."""
    await update_run_stage(state["run_id"], "rejected", "rejected")
    await log_decision(state["run_id"], "pipeline", "pipeline_rejected", {
        "stage": state.get("current_stage"),
    })
    return {"current_stage": "rejected"}


# ---------------------------------------------------------------------------
# HITL gate nodes
# ---------------------------------------------------------------------------
async def hitl_ba(state: PipelineState) -> dict:
    return await _hitl_node(state, "ba")


async def hitl_product(state: PipelineState) -> dict:
    return await _hitl_node(state, "product")


async def hitl_analyst(state: PipelineState) -> dict:
    return await _hitl_node(state, "analyst")


async def hitl_final(state: PipelineState) -> dict:
    return await _hitl_node(state, "final")


# ---------------------------------------------------------------------------
# Routing after each HITL gate
# ---------------------------------------------------------------------------
def _route(state: PipelineState, next_node: str, retry_node: str) -> str:
    status = state.get("hitl_status")
    if status == "approved":
        return next_node
    if status == "rejected":
        return "rejected_node"  # stop the pipeline
    return retry_node  # "changes" -> re-run agent with feedback


def route_after_hitl_ba(state: PipelineState) -> str:
    return _route(state, "product_node", "ba_node")


def route_after_hitl_product(state: PipelineState) -> str:
    return _route(state, "analyst_node", "product_node")


def route_after_hitl_analyst(state: PipelineState) -> str:
    return _route(state, "qa_node", "analyst_node")


def route_after_hitl_final(state: PipelineState) -> str:
    return _route(state, "done_node", "qa_node")


# ---------------------------------------------------------------------------
# Build & compile the graph
# ---------------------------------------------------------------------------
def build_pipeline():
    graph = StateGraph(PipelineState)

    # Nodes
    graph.add_node("ba_node", ba_node)
    graph.add_node("hitl_ba", hitl_ba)
    graph.add_node("product_node", product_node)
    graph.add_node("hitl_product", hitl_product)
    graph.add_node("analyst_node", analyst_node)
    graph.add_node("hitl_analyst", hitl_analyst)
    graph.add_node("qa_node", qa_node)
    graph.add_node("design_node", design_node)
    graph.add_node("hitl_final", hitl_final)
    graph.add_node("done_node", done_node)
    graph.add_node("rejected_node", rejected_node)

    # Edges: BA -> HITL -> Product -> HITL -> Analyst -> HITL -> QA -> Design -> HITL -> Done
    graph.add_edge(START, "ba_node")
    graph.add_edge("ba_node", "hitl_ba")
    graph.add_conditional_edges("hitl_ba", route_after_hitl_ba, {
        "product_node": "product_node",
        "ba_node": "ba_node",
        "rejected_node": "rejected_node",
    })
    graph.add_edge("product_node", "hitl_product")
    graph.add_conditional_edges("hitl_product", route_after_hitl_product, {
        "analyst_node": "analyst_node",
        "product_node": "product_node",
        "rejected_node": "rejected_node",
    })
    graph.add_edge("analyst_node", "hitl_analyst")
    graph.add_conditional_edges("hitl_analyst", route_after_hitl_analyst, {
        "qa_node": "qa_node",
        "analyst_node": "analyst_node",
        "rejected_node": "rejected_node",
    })
    graph.add_edge("qa_node", "design_node")
    graph.add_edge("design_node", "hitl_final")
    graph.add_conditional_edges("hitl_final", route_after_hitl_final, {
        "done_node": "done_node",
        "qa_node": "qa_node",
        "rejected_node": "rejected_node",
    })
    graph.add_edge("done_node", END)
    graph.add_edge("rejected_node", END)

    return graph.compile()


# Compile once at import time
_pipeline = build_pipeline()


async def run_pipeline(run_id: str, brief: str) -> None:
    """Run the full pipeline. Launched as a background task by the API."""
    initial_state: PipelineState = {
        "run_id": run_id,
        "brief": brief,
        "current_stage": "ba",
        "requirements": None,
        "inception": None,
        "user_stories": None,
        "test_cases": None,
        "diagrams": None,
        "hitl_status": None,
        "hitl_feedback": None,
        "error": None,
        "retry_count": 0,
    }

    try:
        await _pipeline.ainvoke(initial_state)
    except Exception as e:
        await update_run_stage(run_id, "error", "error")
        await log_decision(run_id, "pipeline", "pipeline_error", {"error": str(e)})
