from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import asyncpg
from pydantic import BaseModel


class Chart(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    created_at: datetime


class ChatHistory(BaseModel):
    id: UUID
    user_id: UUID
    message: Optional[str] = None
    response: Optional[str] = None
    has_chart: bool = False
    chart_id: Optional[UUID] = None
    created_at: datetime


class Transaction(BaseModel):
    id: UUID
    user_id: UUID
    symbol: Optional[str] = None
    date_time: Optional[datetime] = None
    quantity: Optional[float] = None
    trade_price: Optional[float] = None
    close_price: Optional[float] = None
    proceeds: Optional[float] = None
    commission_fee: Optional[float] = None
    basis: Optional[float] = None
    realized_p_l: Optional[float] = None
    mtm_p_l: Optional[float] = None
    code: Optional[str] = None
    created_at: datetime


class ChartRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
    
    async def insert(self, user_id: UUID, title: Optional[str] = None, type: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> Chart:
        """Insert a new chart record"""
        chart_id = uuid4()
        query = """
            INSERT INTO charts (id, user_id, title, type, data)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, title, type, data, created_at
        """
        record = await self.connection.fetchrow(query, chart_id, user_id, title, type, data)
        return Chart(**dict(record))
    
    async def get_by_user_id(self, user_id: UUID) -> List[Chart]:
        """Get all charts for a user"""
        query = "SELECT * FROM charts WHERE user_id = $1 ORDER BY created_at DESC"
        records = await self.connection.fetch(query, user_id)
        return [Chart(**dict(record)) for record in records]

class ChatHistoryRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
    
    async def insert(self, user_id: UUID, message: Optional[str] = None, response: Optional[str] = None, 
                    has_chart: bool = False, chart_id: Optional[UUID] = None) -> ChatHistory:
        """Insert a new chat history record"""
        history_id = uuid4()
        query = """
            INSERT INTO chat_history (id, user_id, message, response, has_chart, chart_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, user_id, message, response, has_chart, chart_id, created_at
        """
        record = await self.connection.fetchrow(query, history_id, user_id, message, response, has_chart, chart_id)
        return ChatHistory(**dict(record))
  
    async def get_by_user_id(self, user_id: UUID, limit: int = 50) -> List[ChatHistory]:
        """Get chat history for a user"""
        query = "SELECT * FROM chat_history WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2"
        records = await self.connection.fetch(query, user_id, limit)
        return [ChatHistory(**dict(record)) for record in records]
    

class TransactionRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
    
    async def insert(self, user_id: UUID, symbol: Optional[str] = None, date_time: Optional[datetime] = None,
                    quantity: Optional[float] = None, trade_price: Optional[float] = None, close_price: Optional[float] = None,
                    proceeds: Optional[float] = None, commission_fee: Optional[float] = None, basis: Optional[float] = None,
                    realized_p_l: Optional[float] = None, mtm_p_l: Optional[float] = None, code: Optional[str] = None) -> Transaction:
        """Insert a new transaction record"""
        transaction_id = uuid4()
        query = """
            INSERT INTO transactions (id, user_id, symbol, date_time, quantity, trade_price, 
                                    close_price, proceeds, commission_fee, basis, realized_p_l, 
                                    mtm_p_l, code)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id, user_id, symbol, date_time, quantity, trade_price, close_price, 
                     proceeds, commission_fee, basis, realized_p_l, mtm_p_l, code, created_at
        """
        record = await self.connection.fetchrow(
            query, transaction_id, user_id, symbol, date_time, quantity, trade_price,
            close_price, proceeds, commission_fee, basis, realized_p_l, mtm_p_l, code
        )
        return Transaction(**dict(record))
    
    async def get_by_user_id(self, user_id: UUID) -> List[Transaction]:
        """Get all transactions for a user"""
        query = "SELECT * FROM transactions WHERE user_id = $1 ORDER BY date_time DESC"
        records = await self.connection.fetch(query, user_id)
        return [Transaction(**dict(record)) for record in records]
    
class DatabaseRepository:
    """Main repository class that provides access to all table repositories"""
    
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        self.charts = ChartRepository(connection)
        self.chat_history = ChatHistoryRepository(connection)
        self.transactions = TransactionRepository(connection) 