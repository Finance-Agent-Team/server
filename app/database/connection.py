import asyncpg
import os
from typing import Optional
from .repository import DatabaseRepository


class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self):
        self.connection: Optional[asyncpg.Connection] = None
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
    
    async def connect(self) -> asyncpg.Connection:
        """Establish database connection"""
        if self.connection is None:
            self.connection = await asyncpg.connect(self.database_url)
        elif self.connection.is_closed():
            self.connection = await asyncpg.connect(self.database_url)
        return self.connection
    
    async def disconnect(self):
        """Close database connection"""
        if self.connection is not None:
            if not self.connection.is_closed():
                await self.connection.close()
    
    async def get_repository(self) -> DatabaseRepository:
        """Get repository instance with connection"""
        connection = await self.connect()
        return DatabaseRepository(connection)


# Global database connection instance
db_connection = DatabaseConnection() 