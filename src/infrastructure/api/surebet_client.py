"""Surebet API client with cursor incremental polling.

Implementation Requirements:
- Cursor incremental pagination (from ADR-009)
- Optimized API parameters: order=created_at_desc, min-profit=-1
- Use AdaptiveRateLimiter
- Persist cursor in Redis for recovery after restart

Reference:
- docs/05-Implementation.md: Task 5.5
- docs/02-PDR.md: Section 3.3.1 (API Client)
- docs/03-ADRs.md: ADR-009 (Cursor Incremental)
- docs/01-SRS.md: RF-001

TODO: Implement SurebetClient
"""

from typing import List, Optional, Protocol

import aiohttp


class CursorRepository(Protocol):
    """Protocol for cursor persistence."""
    async def get_cursor(self) -> Optional[str]: ...
    async def set_cursor(self, cursor: str) -> bool: ...


class SurebetClient:
    """
    Client for apostasseguras.com surebet API.
    
    Features:
    - Cursor incremental polling (only new picks since last)
    - Adaptive rate limiting
    - Cursor persistence for recovery
    
    API Parameters (from ADR-009):
    - product: surebets
    - order: created_at_desc
    - min-profit: -1
    - limit: 5000
    - cursor: {sort_by}:{id} of last pick
    
    TODO: Implement based on:
    - Task 5.5 in docs/05-Implementation.md
    - ADR-009 in docs/03-ADRs.md
    - RF-001 in docs/01-SRS.md
    - RequestQueue in legacy/RetadorV6.py (line 533)
    """
    
    def __init__(
        self,
        api_url: str,
        api_token: str,
        rate_limiter,  # AdaptiveRateLimiter
        cursor_repository: CursorRepository,
        bookmakers: List[str],
        sports: List[str],
        limit: int = 5000,
    ):
        """
        Initialize API client.
        
        Args:
            api_url: Base URL for API
            api_token: Bearer token for authentication
            rate_limiter: AdaptiveRateLimiter instance
            cursor_repository: Repository for cursor persistence
            bookmakers: List of bookmaker identifiers
            sports: List of sport identifiers
            limit: Maximum results per request
        """
        self._url = api_url
        self._token = api_token
        self._rate_limiter = rate_limiter
        self._cursor_repo = cursor_repository
        self._bookmakers = bookmakers
        self._sports = sports
        self._limit = limit
        self._last_cursor: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def fetch_picks(self) -> List[dict]:
        """
        Fetch picks from API with cursor pagination.
        
        Uses cursor from last call to get only new picks.
        
        Returns:
            List of new surebet records
        
        Reference:
        - ADR-009 for cursor format
        - RF-001 for API parameters
        """
        raise NotImplementedError("SurebetClient.fetch_picks not implemented")
    
    def _build_params(self) -> dict:
        """
        Build API request parameters.
        
        Includes:
        - product: surebets
        - order: created_at_desc
        - min-profit: -1
        - limit: 5000
        - cursor: if available
        - source: bookmakers
        - sport: sports
        """
        raise NotImplementedError("SurebetClient._build_params not implemented")
    
    async def _update_cursor(self, picks: List[dict]) -> None:
        """
        Update cursor from last pick in response.
        
        Cursor format: {sort_by}:{id}
        Persists to Redis for recovery.
        """
        raise NotImplementedError("SurebetClient._update_cursor not implemented")
    
    async def _load_cursor(self) -> None:
        """
        Load persisted cursor from repository.
        
        Called on startup for recovery.
        """
        raise NotImplementedError("SurebetClient._load_cursor not implemented")
    
    async def initialize(self) -> None:
        """
        Initialize client: create session, load cursor.
        """
        raise NotImplementedError("SurebetClient.initialize not implemented")
    
    async def close(self) -> None:
        """
        Close client: cleanup session.
        """
        raise NotImplementedError("SurebetClient.close not implemented")
