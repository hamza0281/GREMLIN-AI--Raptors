"""
Chaos-QA REST API Routes
All HTTP endpoints for starting scans, fetching results, and getting reports.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

from backend.core.personas import get_all_personas, PersonaType
from .scan_manager import scan_manager


router = APIRouter(prefix="/api", tags=["chaos-qa"])


# ─── Request/Response Models ───

class ScanRequest(BaseModel):
    url: str
    personas: Optional[List[str]] = None
    max_actions_per_element: int = 2
    max_pages: int = 1
    headless: bool = True


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str


# ─── Health ───

@router.get("/health")
async def health_check():
    """Check if the API is running."""
    from backend.core.model_client import ChaosModelClient
    client = ChaosModelClient()
    model_ok = await client.check_health()
    await client.close()
    return {
        "status": "healthy",
        "model_available": model_ok,
        "model_name": "qwen2.5:0.5b",
        "active_scans": len([
            s for s in scan_manager.sessions.values()
            if s.status.value == "running"
        ]),
    }


# ─── Personas ───

@router.get("/personas")
async def list_personas():
    """Get all available chaos personas."""
    return {"personas": get_all_personas()}


# ─── Scan Operations ───

@router.post("/scan", response_model=ScanResponse)
async def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new chaos scan. Runs in background, poll /api/scan/{id} for status."""
    # Validate URL
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    # Create scan session
    session = scan_manager.create_scan(
        url=url,
        personas=req.personas,
        max_actions_per_element=req.max_actions_per_element,
        max_pages=req.max_pages,
        headless=req.headless,
    )

    # Run scan in background
    background_tasks.add_task(scan_manager.run_scan, session.scan_id)

    return ScanResponse(
        scan_id=session.scan_id,
        status="queued",
        message=f"Chaos scan queued for {url}. Connect to WebSocket at /ws/{session.scan_id} for real-time updates.",
    )


@router.get("/scan/{scan_id}")
async def get_scan_status(scan_id: str):
    """Get the current status of a scan."""
    session = scan_manager.get_scan(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return session.to_dict()


@router.get("/scan/{scan_id}/events")
async def get_scan_events(scan_id: str, offset: int = 0, limit: int = 100):
    """Get events from a scan (for polling if WebSocket not available)."""
    session = scan_manager.get_scan(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    events = session.events[offset : offset + limit]
    return {
        "scan_id": scan_id,
        "total_events": len(session.events),
        "offset": offset,
        "count": len(events),
        "events": events,
    }


@router.get("/scan/{scan_id}/report")
async def get_scan_report(scan_id: str):
    """Get the full bug report for a completed scan."""
    session = scan_manager.get_scan(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    if session.status.value != "completed":
        raise HTTPException(status_code=400, detail=f"Scan is still {session.status.value}")
    if not session.report:
        raise HTTPException(status_code=404, detail="No report available")

    return session.report


@router.get("/scan/{scan_id}/bugs")
async def get_scan_bugs(scan_id: str):
    """Get just the bugs from a completed scan."""
    session = scan_manager.get_scan(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    if not session.report:
        return {"bugs": [], "total": 0}

    bugs = session.report.get("bugs", [])
    return {
        "scan_id": scan_id,
        "total": len(bugs),
        "bugs": bugs,
    }


@router.get("/scan/{scan_id}/score")
async def get_chaos_score(scan_id: str):
    """Get the chaos resilience score for a completed scan."""
    session = scan_manager.get_scan(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    if not session.report:
        return {"score": None, "message": "Scan not completed yet"}

    return {
        "scan_id": scan_id,
        "chaos_score": session.report.get("chaos_score"),
    }


# ─── All Scans ───

@router.get("/scans")
async def list_scans():
    """List all scan sessions."""
    return {"scans": scan_manager.get_all_scans()}
