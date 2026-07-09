from typing import List
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        """Manages active WebSocket connections for low-latency streaming."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket,
    ):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        # Broadcast message to all active connections
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


# Separate managers
video_ws_manager = WebSocketManager()
alert_ws_manager = WebSocketManager()