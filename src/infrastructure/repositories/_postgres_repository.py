"""PostgreSQL repository for future historical data storage.

NOTE: This is a placeholder for future implementation.
Not part of v2.0 scope.
"""

from typing import List, Optional

from .base import BaseRepository


class PostgresRepository(BaseRepository):
    """
    PostgreSQL repository for historical pick storage.
    
    TODO: Implement for v3.0 features:
    - Pick history
    - Automatic resolution
    - Profitability dashboard
    """
    
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool = None
        raise NotImplementedError("PostgreSQL repository not implemented in v2.0")
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError()
    
    async def exists_any(self, keys: List[str]) -> bool:
        raise NotImplementedError()
    
    async def set(self, key: str, value: str, ttl: int) -> bool:
        raise NotImplementedError()
    
    async def get(self, key: str) -> Optional[str]:
        raise NotImplementedError()
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError()
    
    async def close(self) -> None:
        raise NotImplementedError()
