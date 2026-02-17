from fastapi import APIRouter, HTTPException

from models.schemas import HitlDecisionRequest, HitlGateResponse
from services import db_service

router = APIRouter()


@router.get("/runs/{run_id}/hitl/current", response_model=HitlGateResponse | None)
async def get_current_hitl(run_id: str):
    return await db_service.get_pending_hitl(run_id)


@router.post("/runs/{run_id}/hitl/approve")
async def approve_hitl(run_id: str):
    result = await db_service.resolve_hitl(run_id, "approved", None)
    if not result:
        raise HTTPException(status_code=404, detail="No pending HITL gate")
    return result


@router.post("/runs/{run_id}/hitl/reject")
async def reject_hitl(run_id: str):
    result = await db_service.resolve_hitl(run_id, "rejected", None)
    if not result:
        raise HTTPException(status_code=404, detail="No pending HITL gate")
    return result


@router.post("/runs/{run_id}/hitl/request-changes")
async def request_changes_hitl(run_id: str, req: HitlDecisionRequest):
    result = await db_service.resolve_hitl(run_id, "changes", req.feedback)
    if not result:
        raise HTTPException(status_code=404, detail="No pending HITL gate")
    return result
