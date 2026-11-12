from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from forge.pipeline import generate_project
from forge.rag import build_from_approved, get_index, retrieve
from forge.schemas import ProjectRequest
from forge.service import (
    approve_project,
    get_project_diff,
    github_export,
    run_project_tests,
    run_sandbox_tests,
)
from forge.storage import get_project, initialize_database, list_projects
from forge.streaming import stream_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Forge",
    description=(
        "Forge — A multi-agent AI software engineering team that plans, "
        "builds, tests, and reviews your code."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "forge",
        "version": app.version,
        "features": {
            "repair_loop": True,
            "telemetry": True,
            "streaming": True,
            "diff_viewer": True,
            "github_export": True,
            "docker_sandbox": True,
            "rag": True,
        },
    }


@app.get("/projects")
def get_projects():
    return list_projects()


@app.get("/projects/{project_id}")
def get_project_detail(project_id: str):
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/generate")
async def generate(req: ProjectRequest):
    try:
        return await generate_project(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/generate/stream")
async def generate_stream(req: ProjectRequest):
    """SSE stream of pipeline events (stage/repair/telemetry/done)."""
    return StreamingResponse(
        stream_project(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/projects/{project_id}/approve")
def approve(project_id: str):
    try:
        return approve_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/projects/{project_id}/test")
def test(project_id: str):
    try:
        return run_project_tests(project_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/projects/{project_id}/test/sandbox")
def test_sandbox(project_id: str):
    """Run tests inside a Docker sandbox (no network, restricted resources)."""
    try:
        return run_sandbox_tests(project_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/projects/{project_id}/diff")
def project_diff(project_id: str):
    """Diff current awaiting-approval code vs last approved snapshot."""
    try:
        return get_project_diff(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/projects/{project_id}/telemetry")
def project_telemetry(project_id: str):
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    telemetry = project["result"].get("telemetry")
    if telemetry is None:
        raise HTTPException(status_code=404, detail="No telemetry for this project")
    return telemetry


@app.post("/projects/{project_id}/export/github")
def export_github(project_id: str, repo_name: str = Query(default=None),
                  visibility: str = Query(default=None)):
    try:
        return github_export(project_id, repo_name=repo_name, visibility=visibility)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/rag/search")
def rag_search(q: str = Query(..., min_length=2), k: int = Query(default=5)):
    return retrieve(q, k)


@app.post("/rag/rebuild")
def rag_rebuild():
    count = build_from_approved()
    return {"rebuilt": True, "documents": count}


@app.get("/rag/stats")
def rag_stats():
    idx = get_index()
    return {"documents": len(idx)}
