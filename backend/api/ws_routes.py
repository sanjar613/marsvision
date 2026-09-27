from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import random

ws_router = APIRouter()

@ws_router.websocket("/ws/alerts")
async def alerts_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(random.uniform(5.0, 15.0))
            alert_payload = {
                "type": "CRITICAL_ALERT",
                "timestamp": asyncio.get_event_loop().time(),
                "data": {
                    "event": "ACCIDENT",
                    "camera_id": "CAM_01",
                    "risk_score": 0.98,
                    "message": "Traffic accident detected at the intersection!"
                }
            }
            await websocket.send_json(alert_payload)
    except WebSocketDisconnect:
        pass