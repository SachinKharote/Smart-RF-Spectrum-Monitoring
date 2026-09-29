import json
from typing import Set

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        message = json.dumps(payload)
        stale = []
        for connection in list(self.connections):
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


ws_manager = WebSocketManager()
