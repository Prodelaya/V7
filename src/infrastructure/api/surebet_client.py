"""Surebet API client with cursor incremental pagination."""

import asyncio
import logging
from typing import List, Optional
from dataclasses import dataclass

import aiohttp

from .rate_limiter import AdaptiveRateLimiter


logger = logging.getLogger(__name__)


@dataclass
class CursorState:
    """State for cursor-based pagination."""
    sort_by: str = "created_at"
    last_id: Optional[str] = None
    
    @property
    def cursor_string(self) -> Optional[str]:
        """Generate cursor string for API."""
        if self.last_id:
            return f"{self.sort_by}:{self.last_id}"
        return None
    
    @classmethod
    def from_string(cls, cursor: str) -> "CursorState":
        """Parse cursor string."""
        parts = cursor.split(":", 1)
        if len(parts) == 2:
            return cls(sort_by=parts[0], last_id=parts[1])
        return cls()


class SurebetClient:
    """
    Client for fetching surebets from API.
    
    Features:
    - Cursor-based incremental pagination
    - Adaptive rate limiting
    - Automatic session management
    """
    
    def __init__(
        self,
        api_url: str,
        api_token: str,
        rate_limiter: AdaptiveRateLimiter,
        timeout: int = 30,
    ):
        self._api_url = api_url
        self._api_token = api_token
        self._rate_limiter = rate_limiter
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._cursor = CursorState()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
        return self._session
    
    async def fetch_surebets(
        self,
        bookmakers: List[str],
        sports: List[str],
        limit: int = 5000,
        min_profit: float = -1.0,
    ) -> List[dict]:
        """
        Fetch surebets from API using cursor pagination.
        
        Args:
            bookmakers: List of bookmaker IDs
            sports: List of sport IDs
            limit: Maximum records per request
            min_profit: Minimum profit filter
            
        Returns:
            List of surebet records
        """
        await self._rate_limiter.acquire()
        
        params = {
            "product": "surebets",
            "limit": limit,
            "source": "|".join(bookmakers),
            "sport": "|".join(sports),
            "order": "created_at_desc",
            "min-profit": min_profit,
        }
        
        # Add cursor if available
        if self._cursor.cursor_string:
            params["cursor"] = self._cursor.cursor_string
        
        try:
            session = await self._get_session()
            
            async with session.get(self._api_url, params=params) as response:
                # Handle rate limiting
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    self._rate_limiter.on_rate_limit(retry_after)
                    return []
                
                if response.status != 200:
                    logger.error(f"API error: {response.status}")
                    return []
                
                data = await response.json()
                records = data.get("records", [])
                
                # Update cursor from response
                if records:
                    self._update_cursor(records[-1])
                
                self._rate_limiter.on_success()
                return records
                
        except asyncio.TimeoutError:
            logger.error("API request timeout")
            return []
        except Exception as e:
            logger.error(f"API request error: {e}")
            return []
    
    def _update_cursor(self, last_record: dict) -> None:
        """Update cursor state from last record."""
        record_id = last_record.get("id")
        if record_id:
            self._cursor.last_id = str(record_id)
    
    def reset_cursor(self) -> None:
        """Reset cursor to start from beginning."""
        self._cursor = CursorState()
    
    def set_cursor(self, cursor_string: str) -> None:
        """Set cursor from string (for recovery)."""
        self._cursor = CursorState.from_string(cursor_string)
    
    def get_cursor(self) -> Optional[str]:
        """Get current cursor string."""
        return self._cursor.cursor_string
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
