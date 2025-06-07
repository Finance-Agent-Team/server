from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.database.connection import db_connection
from app.database.repository import DatabaseRepository

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatSendRequest(BaseModel):
    message: str
    user_id: UUID


async def get_db_repository() -> DatabaseRepository:
    """Dependency to get database repository"""
    return await db_connection.get_repository()


@router.get("/history")
async def get_chat_history(
    user_id: UUID,
    limit: int = 50,
    db: DatabaseRepository = Depends(get_db_repository)
):
    """Retrieve conversation history for a user"""
    try:
        chat_history = await db.chat_history.get_by_user_id(user_id, limit)
        return {
            "status": "success",
            "chat_history": [
                {
                    "id": chat.id,
                    "message": chat.message,
                    "response": chat.response,
                    "has_chart": chat.has_chart,
                    "chart_id": chat.chart_id,
                    "created_at": chat.created_at
                }
                for chat in chat_history
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@router.post("/send")
async def send_message(
    request: ChatSendRequest,
    db: DatabaseRepository = Depends(get_db_repository)
):
    """Send message to agent and receive response"""
    return {"status": "ok", "message": "Chat send endpoint ready"} 