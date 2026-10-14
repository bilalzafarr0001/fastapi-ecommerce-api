"""
Notifications routes: a WebSocket for live updates + a small demo page.

Unlike a normal HTTP request, a WebSocket stays open, so the SERVER can
push messages to the browser whenever something happens (e.g. an admin
ships your order).
"""
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse

from app.core.security import decode_token
from app.modules.notifications.manager import notification_manager

router = APIRouter(prefix="/notifications", tags=["Notifications"])

DEMO_PAGE = Path(__file__).with_name("demo.html").read_text(encoding="utf-8")


@router.websocket("/ws")
async def notifications_websocket(websocket: WebSocket, token: str):
    """
    Connect with: ws://127.0.0.1:8000/api/v1/notifications/ws?token=<access_token>

    Browsers can't send an Authorization header on a WebSocket, so the token
    is passed as a query parameter instead. (URLs often end up in server logs,
    which is one more reason to keep access tokens short-lived.)
    """
    user_id = decode_token(token, expected_type="access")
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await notification_manager.connect(user_id, websocket)
    try:
        while True:
            # We don't expect messages from the client: waiting here simply
            # keeps the connection open until the client disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_manager.disconnect(user_id, websocket)


@router.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def notifications_demo_page():
    """A tiny HTML page to try the WebSocket in your browser."""
    return DEMO_PAGE
