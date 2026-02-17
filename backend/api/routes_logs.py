from fastapi import APIRouter

from models.schemas import DecisionLogEntry
from services import db_service

router = APIRouter()


@router.get("/runs/{run_id}/logs", response_model=list[DecisionLogEntry])
async def get_decision_logs(run_id: str):
    return await db_service.list_decision_logs(run_id)
