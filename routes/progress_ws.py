# routes/progress_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()

# Dict: upload_id → list of websockets
connected_websockets = {}

@router.websocket("/ws/progress/{upload_id}")
async def websocket_endpoint(websocket: WebSocket, upload_id: str):
    await websocket.accept()
    if upload_id not in connected_websockets:
        connected_websockets[upload_id] = []
    connected_websockets[upload_id].append(websocket)
    print(f"[WebSocket] Client connected for upload_id={upload_id} — total: {len(connected_websockets[upload_id])}")

    try:
        while True:
            # Keep WebSocket alive
            await asyncio.sleep(1)
    except WebSocketDisconnect: 
        connected_websockets[upload_id].remove(websocket)
        print(f"[WebSocket] Client disconnected for upload_id={upload_id} — remaining: {len(connected_websockets[upload_id])}")
        
        # Cleanup empty list
        if len(connected_websockets[upload_id]) == 0:
            del connected_websockets[upload_id]
