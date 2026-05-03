"""
Chaos-QA WebSocket Handler
Real-time event streaming for live chaos scan monitoring.
Clients connect to /ws/{scan_id} and receive events as they happen.
"""

import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

from backend.core.chaos_engine import ScanEvent
from .scan_manager import scan_manager


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # scan_id -> set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, scan_id: str):
        """Accept a WebSocket connection and register it for a scan."""
        await websocket.accept()
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = set()
        self.active_connections[scan_id].add(websocket)

        # Register as event listener on scan manager
        async def event_handler(event: ScanEvent):
            await self.send_event(scan_id, event)

        scan_manager.add_event_listener(scan_id, event_handler)

        # Store the handler reference for cleanup
        websocket._chaos_event_handler = event_handler

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {"scan_id": scan_id, "message": "Connected to Chaos-QA live feed"},
        })

        # Send any past events that already happened
        session = scan_manager.get_scan(scan_id)
        if session and session.events:
            await websocket.send_json({
                "type": "history",
                "data": {
                    "events": session.events[-50:],  # Last 50 events
                    "total": len(session.events),
                },
            })

    async def disconnect(self, websocket: WebSocket, scan_id: str):
        """Remove a WebSocket connection."""
        if scan_id in self.active_connections:
            self.active_connections[scan_id].discard(websocket)
            if not self.active_connections[scan_id]:
                del self.active_connections[scan_id]

        # Remove event listener
        handler = getattr(websocket, "_chaos_event_handler", None)
        if handler:
            scan_manager.remove_event_listener(scan_id, handler)

    async def send_event(self, scan_id: str, event: ScanEvent):
        """Broadcast an event to all connected clients for a scan."""
        connections = self.active_connections.get(scan_id, set())
        dead_connections = set()

        for websocket in connections:
            try:
                await websocket.send_json(event.to_dict())
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for ws in dead_connections:
            await self.disconnect(ws, scan_id)


# Global singleton
ws_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    """WebSocket endpoint handler — called from main.py."""
    await ws_manager.connect(websocket, scan_id)
    try:
        while True:
            # Keep connection alive, listen for client messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # Handle client commands
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg.get("type") == "get_status":
                    session = scan_manager.get_scan(scan_id)
                    if session:
                        await websocket.send_json({
                            "type": "status",
                            "data": session.to_dict(),
                        })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, scan_id)
    except Exception:
        await ws_manager.disconnect(websocket, scan_id)
