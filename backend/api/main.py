"""
GremlinAI — FastAPI Main Application
Entry point for the backend server.

Run with:
  python -m backend.api.main
  OR
  uvicorn backend.api.main:app --reload --port 8000
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .routes import router as api_router
from .websocket import websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle."""
    print("\n" + "="*50)
    print("  GREMLIN-AI API Server Starting...")
    print("  Gremlins break your app before users do")
    print("="*50)

    # Ensure reports directory exists
    os.makedirs("./reports", exist_ok=True)
    os.makedirs("./reports/screenshots", exist_ok=True)

    yield

    print("\n  GremlinAI shutting down...")


# Create FastAPI app
app = FastAPI(
    title="GremlinAI",
    description=(
        "Autonomous chaos testing powered by a deliberately tiny LLM. "
        "The model's hallucinations ARE the feature — gremlins break your app before users do."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)


# WebSocket endpoint
@app.websocket("/ws/{scan_id}")
async def ws_endpoint(websocket: WebSocket, scan_id: str):
    """WebSocket endpoint for real-time scan updates."""
    await websocket_endpoint(websocket, scan_id)


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "GremlinAI",
        "tagline": "The AI that breaks your app before users do",
        "version": "1.0.0",
        "model": "qwen2.5:0.5b (Tier 1 — Absolute Garage)",
        "endpoints": {
            "health": "/api/health",
            "personas": "/api/personas",
            "start_scan": "POST /api/scan",
            "scan_status": "/api/scan/{scan_id}",
            "scan_report": "/api/scan/{scan_id}/report",
            "scan_bugs": "/api/scan/{scan_id}/bugs",
            "scan_score": "/api/scan/{scan_id}/score",
            "scan_events": "/api/scan/{scan_id}/events",
            "all_scans": "/api/scans",
            "websocket": "ws://localhost:8000/ws/{scan_id}",
        },
    }


# Run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
