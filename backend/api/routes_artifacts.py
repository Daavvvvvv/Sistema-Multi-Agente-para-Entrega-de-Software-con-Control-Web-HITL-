from fastapi import APIRouter, HTTPException

from models.schemas import ArtifactResponse
from services import db_service

router = APIRouter()


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactResponse])
async def list_artifacts(run_id: str):
    return await db_service.list_artifacts(run_id)


@router.get("/runs/{run_id}/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(run_id: str, artifact_id: str):
    artifact = await db_service.get_artifact(run_id, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.get("/runs/{run_id}/diagrams/{diagram_type}")
async def get_diagram(run_id: str, diagram_type: str):
    if diagram_type not in ("er", "sequence"):
        raise HTTPException(status_code=400, detail="diagram_type must be 'er' or 'sequence'")
    diagram = await db_service.get_diagram(run_id, diagram_type)
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return diagram
