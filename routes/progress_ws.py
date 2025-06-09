# routes/progress_ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Simple list to track connected clients
connected_websockets = []

@router.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    print(f"[WebSocket] Client connected: {len(connected_websockets)} clients")

    try:
        while True:
            await websocket.receive_text()  # We don't use it, but keeps connection alive
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
        print(f"[WebSocket] Client disconnected: {len(connected_websockets)} clients")
