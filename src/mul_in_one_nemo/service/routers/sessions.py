"""Session-related API routes."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from mul_in_one_nemo.service.dependencies import get_session_repository, get_session_service
from mul_in_one_nemo.service.models import SessionMessage, SessionRecord
from mul_in_one_nemo.service.session_service import SessionNotFoundError, SessionService

router = APIRouter(tags=["sessions"])


class MessagePayload(BaseModel):
    content: str
    target_personas: Optional[List[str]] = None


class SessionUpdatePayload(BaseModel):
    user_persona: Optional[str] = None


def _serialize_session(record: SessionRecord) -> dict[str, object | None]:
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "user_id": record.user_id,
        "created_at": record.created_at.isoformat(),
        "user_persona": record.user_persona,
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    tenant_id: str,
    user_id: str,
    user_persona: str | None = None,
    service: SessionService = Depends(get_session_service),
):
    session_id = await service.create_session(tenant_id=tenant_id, user_id=user_id, user_persona=user_persona)
    return {"session_id": session_id}


@router.get("/sessions", status_code=status.HTTP_200_OK)
async def list_sessions(
    tenant_id: str,
    user_id: str,
    repository=Depends(get_session_repository),
):
    sessions = await repository.list_sessions(tenant_id=tenant_id, user_id=user_id)
    return [_serialize_session(s) for s in sessions]


@router.get("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def get_session(session_id: str, repository=Depends(get_session_repository)):
    record = await repository.get(session_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return _serialize_session(record)


@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_message(
    session_id: str,
    payload: MessagePayload,
    service: SessionService = Depends(get_session_service),
):
    message = SessionMessage(
        session_id=session_id, 
        content=payload.content, 
        sender="user",
        target_personas=payload.target_personas
    )
    try:
        await service.enqueue_message(message)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc
    return {"session_id": session_id, "status": "queued"}


@router.get("/sessions/{session_id}/messages", status_code=status.HTTP_200_OK)
async def list_messages(
    session_id: str,
    limit: int = 50,
    repository=Depends(get_session_repository),
):
    record = await repository.get(session_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    messages = await repository.list_messages(session_id, limit=limit)
    return {
        "session_id": session_id,
        "user_persona": record.user_persona,
        "messages": [
            {
                "id": message.id,
                "sender": message.sender,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in messages
        ],
    }


@router.patch("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def update_session(
    session_id: str,
    payload: SessionUpdatePayload,
    service: SessionService = Depends(get_session_service),
):
    try:
        record = await service.update_user_persona(session_id, payload.user_persona)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc
    return _serialize_session(record)


@router.websocket("/ws/sessions/{session_id}")
async def session_stream(websocket: WebSocket, session_id: str, service: SessionService = Depends(get_session_service)):
    await websocket.accept()
    try:
        stream = await service.stream_responses(session_id)
    except SessionNotFoundError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        return
    try:
        async for event in stream:
            await websocket.send_json({"event": event.event, "data": event.data})
    except WebSocketDisconnect:
        pass
    finally:
        await stream.aclose()
