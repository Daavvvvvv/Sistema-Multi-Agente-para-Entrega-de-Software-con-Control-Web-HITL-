from fastapi import APIRouter, HTTPException

from models.schemas import CreateRunRequest, RunResponse
from services import db_service

router = APIRouter()


@router.post("/runs", response_model=RunResponse)
async def create_run(req: CreateRunRequest):
    run = await db_service.create_run(req.brief)
    return run


@router.get("/runs", response_model=list[RunResponse])
async def list_runs():
    return await db_service.list_runs()


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    run = await db_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/status")
async def get_run_status(run_id: str):
    status = await db_service.get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run not found")
    return status
