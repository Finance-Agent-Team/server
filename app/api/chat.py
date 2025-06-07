from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel
import json

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
        
        # Build response with chart data when available
        response_data: List[Dict[str, Any]] = []
        for chat in chat_history:
            chat_item: Dict[str, Any] = {
                "id": chat.id,
                "message": chat.message,
                "response": chat.response,
                "has_chart": chat.has_chart,
                "created_at": chat.created_at
            }
            
            # If there's a chart associated, fetch and include the chart data
            if chat.has_chart and chat.chart_id:
                # Get chart data directly from database to avoid Pydantic validation issues
                query = "SELECT type, data FROM charts WHERE id = $1"
                chart_record = await db.connection.fetchrow(query, chat.chart_id)
                
                if chart_record:
                    chart_data = chart_record['data']
                    # Parse JSON string to dict if needed
                    if isinstance(chart_data, str):
                        try:
                            chart_data = json.loads(chart_data)
                        except json.JSONDecodeError:
                            chart_data = None
                    
                    chat_item["chart"] = {
                        "type": chart_record['type'],
                        "data": chart_data
                    }
                else:
                    chat_item["chart"] = None
            else:
                chat_item["chart"] = None
                
            response_data.append(chat_item)
        
        return {
            "status": "success",
            "chat_history": response_data
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