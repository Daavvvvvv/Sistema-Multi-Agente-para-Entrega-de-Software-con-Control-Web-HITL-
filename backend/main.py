from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api.routes_runs import router as runs_router
from api.routes_artifacts import router as artifacts_router
from api.routes_hitl import router as hitl_router
from api.routes_logs import router as logs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Multi-Agent SDLC Pipeline", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router, prefix="/api")
app.include_router(artifacts_router, prefix="/api")
app.include_router(hitl_router, prefix="/api")
app.include_router(logs_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
