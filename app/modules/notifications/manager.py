"""
Notification manager: keeps track of the open WebSocket connections.

This module plays the "controller" role for notifications. Other modules
(e.g. orders) call `notification_manager.send_to_user(...)` to push a live
message to a user's browser.

Note: connections are stored in memory, so this works with a single server
process. With several processes/servers you would use Redis Pub/Sub instead.
"""
from fastapi import WebSocket


class NotificationManager:
    def __init__(self) -> None:
        # user_id -> open connections (a user can have several tabs open)
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        user_connections = self.connections.get(user_id, [])
        if websocket in user_connections:
            user_connections.remove(websocket)
        if not user_connections:
            self.connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict) -> None:
        # Iterate over a copy, because `disconnect` may change the list.
        for websocket in list(self.connections.get(user_id, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(user_id, websocket)  # the browser tab was closed


# One shared instance for the whole app.
notification_manager = NotificationManager()
