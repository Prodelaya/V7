"""Base repository abstract class.

Implementation Requirements:
- Define interface for data persistence
- Methods: exists(), set(), get(), delete()
- Batch operations for efficiency

Reference:
- docs/05-Implementation.md: Task 5.1
- docs/02-PDR.md: Section 4.3 (Repository Pattern)

TODO: Implement BaseRepository
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseRepository(ABC):
    """
    Abstract base class for data repositories.
    
    Defines the interface for pick persistence and deduplication.
    
    TODO: Implement based on:
    - Task 5.1 in docs/05-Implementation.md
    """
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Unique key to check
            
        Returns:
            True if key exists
        """
        pass
    
    @abstractmethod
    async def exists_any(self, keys: List[str]) -> bool:
        """
        Check if any of the keys exist.
        
        Args:
            keys: List of keys to check
            
        Returns:
            True if any key exists
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> bool:
        """
        Set key with TTL.
        
        Args:
            key: Unique key
            value: Value to store
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """
        Get value by key.
        
        Args:
            key: Unique key
            
        Returns:
            Value if exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete key.
        
        Args:
            key: Unique key
            
        Returns:
            True if deleted
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connection."""
        pass
