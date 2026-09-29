from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.state.store import event_hub

router = APIRouter(tags=["live"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = event_hub.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        event_hub.unsubscribe(queue)
