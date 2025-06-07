from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from pydantic import BaseModel

from app.database.connection import db_connection
from app.database.repository import DatabaseRepository

router = APIRouter(tags=["dashboard"])


class ChartCreateRequest(BaseModel):
    user_id: UUID
    data_request: str


async def get_db_repository() -> DatabaseRepository:
    """Dependency to get database repository"""
    return await db_connection.get_repository()


@router.get("/dashboard")
async def get_user_charts(
    user_id: UUID,
    db: DatabaseRepository = Depends(get_db_repository)
):
    """List all user-generated charts"""
    return {"status": "ok", "message": "Dashboard charts endpoint ready"}


@router.post("/dashboard/chart")
async def create_chart(
    request: ChartCreateRequest,
    db: DatabaseRepository = Depends(get_db_repository)
):
    """Request generation of a new chart"""
    return {"status": "ok", "message": "Chart creation endpoint ready"} 