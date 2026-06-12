import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.websocket("/dashboard")
async def dashboard_socket(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        from fastapi.security import HTTPAuthorizationCredentials

        current = get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), db)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            summary = MonitoringService(db).dashboard_summary(current.organization_id)
            await websocket.send_json(summary.model_dump())
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
