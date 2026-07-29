"""Workflow-scoped WebSocket event delivery."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, workflow_id: str) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[workflow_id].add(ws)

    async def disconnect(self, ws: WebSocket, workflow_id: str) -> None:
        async with self._lock:
            connections = self._connections.get(workflow_id)
            if connections is None:
                return
            connections.discard(ws)
            if not connections:
                self._connections.pop(workflow_id, None)

    async def broadcast(self, workflow_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._connections.get(workflow_id, ()))
        stale: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(event)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.disconnect(ws, workflow_id)


manager = ConnectionManager()


@router.websocket("/ws/{workflow_id}")
async def ws_endpoint(ws: WebSocket, workflow_id: str) -> None:
    await manager.connect(ws, workflow_id)
    try:
        await ws.send_json(
            {"type": "connected", "workflow_id": workflow_id}
        )
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws, workflow_id)
