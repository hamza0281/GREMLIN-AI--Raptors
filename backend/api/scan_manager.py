"""
Chaos-QA Scan Manager
Manages scan sessions — starts scans, tracks progress, stores results.
Acts as the bridge between API routes and the ChaosEngine.
"""

import asyncio
import uuid
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from backend.core.chaos_engine import ChaosEngine, ScanConfig, ScanEvent
from backend.core.personas import PersonaType, ALL_PERSONA_TYPES


class ScanStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScanSession:
    """A single chaos scan session."""
    scan_id: str
    url: str
    status: ScanStatus
    created_at: float
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    personas: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "url": self.url,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration": (
                round((self.finished_at or time.time()) - (self.started_at or self.created_at), 1)
            ),
            "personas": self.personas,
            "event_count": len(self.events),
            "bug_count": (
                self.report.get("summary", {}).get("total_bugs", 0) if self.report else 0
            ),
            "chaos_score": self.report.get("chaos_score") if self.report else None,
        }


class ScanManager:
    """Manages all scan sessions."""

    def __init__(self):
        self.sessions: Dict[str, ScanSession] = {}
        self._event_listeners: Dict[str, List[Callable]] = {}  # scan_id -> [callbacks]

    def create_scan(
        self,
        url: str,
        personas: List[str] = None,
        max_actions_per_element: int = 2,
        max_pages: int = 1,
        headless: bool = True,
    ) -> ScanSession:
        """Create a new scan session."""
        scan_id = str(uuid.uuid4())[:8]

        # Validate personas
        valid_personas = []
        if personas:
            for p in personas:
                try:
                    valid_personas.append(PersonaType(p))
                except ValueError:
                    pass
        if not valid_personas:
            valid_personas = list(ALL_PERSONA_TYPES)

        session = ScanSession(
            scan_id=scan_id,
            url=url,
            status=ScanStatus.QUEUED,
            created_at=time.time(),
            personas=[p.value for p in valid_personas],
            config={
                "max_actions_per_element": max_actions_per_element,
                "max_pages": max_pages,
                "headless": headless,
            },
        )
        self.sessions[scan_id] = session
        return session

    def add_event_listener(self, scan_id: str, callback: Callable):
        """Register a callback for real-time scan events (WebSocket)."""
        if scan_id not in self._event_listeners:
            self._event_listeners[scan_id] = []
        self._event_listeners[scan_id].append(callback)

    def remove_event_listener(self, scan_id: str, callback: Callable):
        """Remove an event listener."""
        if scan_id in self._event_listeners:
            self._event_listeners[scan_id] = [
                cb for cb in self._event_listeners[scan_id] if cb != callback
            ]

    async def _broadcast_event(self, scan_id: str, event: ScanEvent):
        """Send event to all listeners for a scan."""
        session = self.sessions.get(scan_id)
        if session:
            session.events.append(event.to_dict())

        listeners = self._event_listeners.get(scan_id, [])
        for callback in listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception:
                pass  # Don't let listener errors break the scan

    async def run_scan(self, scan_id: str) -> Dict[str, Any]:
        """Execute a scan session."""
        session = self.sessions.get(scan_id)
        if not session:
            return {"error": "Scan not found"}

        session.status = ScanStatus.RUNNING
        session.started_at = time.time()

        try:
            engine = ChaosEngine()

            # Wire up events
            async def on_engine_event(event: ScanEvent):
                await self._broadcast_event(scan_id, event)

            engine.on_event(on_engine_event)

            # Build config
            config = ScanConfig(
                url=session.url,
                personas=[PersonaType(p) for p in session.personas],
                max_actions_per_element=session.config.get("max_actions_per_element", 2),
                max_pages=session.config.get("max_pages", 1),
                headless=session.config.get("headless", True),
                output_dir="./reports",
            )

            report = await engine.run_scan(config)

            session.report = report
            session.status = ScanStatus.COMPLETED
            session.finished_at = time.time()

            return report

        except Exception as e:
            session.status = ScanStatus.FAILED
            session.error = str(e)
            session.finished_at = time.time()
            return {"error": str(e)}

    def get_scan(self, scan_id: str) -> Optional[ScanSession]:
        """Get a scan session by ID."""
        return self.sessions.get(scan_id)

    def get_all_scans(self) -> List[Dict[str, Any]]:
        """Get all scan sessions."""
        return [s.to_dict() for s in self.sessions.values()]


# Global singleton
scan_manager = ScanManager()
