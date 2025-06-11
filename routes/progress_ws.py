# routes/progress_ws.py

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Simple list to track connected clients
connected_websockets = []


@router.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"[WebSocket] Client connected")

    try:
        # Simulate sending progress updates
        for i in range(0, 101, 10):
            await websocket.send_json({
                "progress": i,
                "status": f"Processing... {i}%",
            })
            await asyncio.sleep(0.5)  # Simulate work
        await websocket.send_json({
            "progress": 100,
            "status": "DONE 🚀",
        })
        await websocket.close()
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected")
