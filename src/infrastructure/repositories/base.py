"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, List


class BaseRepository(ABC):
    """
    Abstract base class for repositories.
    
    Defines interface for pick persistence and deduplication.
    """
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def exists_any(self, keys: List[str]) -> bool:
        """Check if any of the keys exist."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> bool:
        """Set key with TTL."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connection."""
        pass
