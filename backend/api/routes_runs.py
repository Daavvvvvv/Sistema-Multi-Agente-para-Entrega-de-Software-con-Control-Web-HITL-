from fastapi import APIRouter, BackgroundTasks, HTTPException

from models.schemas import CreateRunRequest, RunResponse
from services import db_service
from agents.graph import run_pipeline

router = APIRouter()


@router.post("/runs", response_model=RunResponse)
async def create_run(req: CreateRunRequest, background_tasks: BackgroundTasks):
    run = await db_service.create_run(req.brief)
    background_tasks.add_task(run_pipeline, run["id"], req.brief)
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
