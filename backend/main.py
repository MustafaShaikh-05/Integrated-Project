"""
FastAPI entry point for InsureVision AI.

Exposes GenAI and agentic JSON APIs, a health check, and serves the static SPA
from ``frontend/index.html`` at the site root.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.agentic_module.agent_service import run_insurance_agents
from backend.genai_module.genai_service import generate_insurance_content

# Load .env from project root (parent of ``backend/``).
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="InsureVision AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"


class GenAIRequest(BaseModel):
    """Payload for ``POST /api/genai``."""

    query: str = Field(..., min_length=1)


class AgentRequest(BaseModel):
    """Payload for ``POST /api/agent``."""

    age: int = Field(..., ge=0, le=120)
    city: str = Field(..., min_length=1)
    budget: int = Field(..., ge=0)
    type: str = Field(..., min_length=1)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe for Docker/Kubernetes and monitoring."""
    return {"status": "ok"}


@app.post("/api/genai")
def api_genai(body: GenAIRequest) -> dict[str, str]:
    """Generate insurance explanation text plus a Pollinations image URL."""
    try:
        return generate_insurance_content(body.query)
    except Exception as exc:  # noqa: BLE001 — surface a clean API error
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/agent")
def api_agent(body: AgentRequest) -> dict:
    """Run the multi-step insurance advisor workflow."""
    try:
        return run_insurance_agents(
            age=body.age,
            city=body.city,
            budget=body.budget,
            insurance_type=body.type,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def serve_index() -> FileResponse:
    """Serve the single-page frontend at ``/``."""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="frontend/index.html missing")
    return FileResponse(index_path)
