from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from uuid import UUID

from app.database.connection import db_connection
from app.database.repository import DatabaseRepository

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def get_db_repository() -> DatabaseRepository:
    """Dependency to get database repository"""
    return await db_connection.get_repository()


@router.post("/upload")
async def upload_transactions_pdf(
    user_id: UUID,
    file: UploadFile = File(...),
    db: DatabaseRepository = Depends(get_db_repository)
):
    """Upload PDF of investment transactions and parse them"""
    return {"status": "ok", "message": "Transaction upload endpoint ready"}


@router.get("")
async def get_transactions(
    user_id: UUID,
    db: DatabaseRepository = Depends(get_db_repository)
):
    """Fetch all parsed transactions for a user"""
    return {"status": "ok", "message": "Get transactions endpoint ready"} 