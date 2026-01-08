"""Surebet API client with cursor incremental polling.

Implementation Requirements:
- Cursor incremental pagination (from ADR-009)
- Optimized API parameters from Settings.api_query (ADR-015)
- Use AdaptiveRateLimiter (ADR-010)
- Persist cursor in Redis for recovery after restart

Reference:
- docs/05-Implementation.md: Task 5B.2
- docs/02-PDR.md: Section 3.3.1 (API Client)
- docs/03-ADRs.md: ADR-009, ADR-010, ADR-015
- docs/08-API-Documentation.md: API parameters and cursor format
- docs/01-SRS.md: RF-001, RF-002
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Protocol

import aiohttp

if TYPE_CHECKING:
    from src.config.settings import APIQuerySettings
    from src.infrastructure.api.rate_limiter import AdaptiveRateLimiter


class CursorRepository(Protocol):
    """Protocol for cursor persistence."""

    async def get_cursor(self) -> Optional[str]:
        ...

    async def set_cursor(self, cursor: str) -> bool:
        ...


@dataclass
class CursorState:
    """State for cursor incremental pagination (ADR-009).

    Format: {sort_by}:{id}
    - API uses numeric sort_by (e.g., "4609118910833099900:785141488")
    - Can also use string sort_by (e.g., "created_at:12345")
    Both formats are supported.

    Example:
        >>> cursor = CursorState(sort_by="created_at", last_id="12345")
        >>> cursor.cursor_string
        'created_at:12345'
        >>> CursorState.from_string("created_at:12345")
        CursorState(sort_by='created_at', last_id='12345')
    """

    sort_by: str = "created_at"
    last_id: Optional[str] = None

    @property
    def cursor_string(self) -> Optional[str]:
        """Generate cursor string for API request.

        Returns:
            Cursor string in format '{sort_by}:{id}' or None if no last_id.
        """
        if self.last_id is None:
            return None
        return f"{self.sort_by}:{self.last_id}"

    @classmethod
    def from_string(cls, cursor_str: str) -> "CursorState":
        """Parse cursor from string.

        Args:
            cursor_str: Cursor string in format '{sort_by}:{id}'

        Returns:
            CursorState instance
        """
        parts = cursor_str.split(":", 1)
        if len(parts) == 2:
            return cls(sort_by=parts[0], last_id=parts[1])
        return cls()


class SurebetClient:
    """Client for apostasseguras.com surebet API.

    Features:
    - Cursor incremental polling (only new picks since last request)
    - Adaptive rate limiting integration
    - Cursor persistence for recovery after restart
    - Configurable API parameters from Settings

    API Parameters (from ADR-009, ADR-015):
    - product: surebets
    - outcomes: 2 (only 2-leg surebets)
    - order: created_at_desc
    - min/max-profit, min/max-odds: from Settings
    - hide-different-rules: true
    - startAge: PT10M (configurable)
    - cursor: {sort_by}:{id} of last pick

    Example:
        >>> client = SurebetClient(
        ...     api_url="https://api.apostasseguras.com/request",
        ...     api_token="xxx",
        ...     rate_limiter=AdaptiveRateLimiter(),
        ... )
        >>> await client.initialize()
        >>> records = await client.fetch_surebets(
        ...     bookmakers=["pinnaclesports", "retabet"],
        ...     sports=["Football"],
        ... )
        >>> await client.close()
    """

    def __init__(
        self,
        api_url: str,
        api_token: str,
        rate_limiter: "AdaptiveRateLimiter",
        cursor_repository: Optional[CursorRepository] = None,
        api_query: Optional["APIQuerySettings"] = None,
        bookmakers: Optional[List[str]] = None,
        sports: Optional[List[str]] = None,
    ):
        """Initialize API client.

        Args:
            api_url: Base URL for API (e.g., https://api.apostasseguras.com/request)
            api_token: Bearer token for authentication
            rate_limiter: AdaptiveRateLimiter instance for rate limit handling
            cursor_repository: Optional repository for cursor persistence (Redis)
            api_query: Optional APIQuerySettings for configurable params from .env
            bookmakers: Optional list of bookmaker identifiers
            sports: Optional list of sport identifiers
        """
        self._url = api_url
        self._token = api_token
        self._rate_limiter = rate_limiter
        self._cursor_repo = cursor_repository
        self._api_query = api_query
        self._bookmakers = bookmakers or []
        self._sports = sports or []
        self._cursor = CursorState()
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize client: create session, load cursor.

        Creates an aiohttp session with proper headers and loads
        any persisted cursor from the repository.
        """
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=aiohttp.ClientTimeout(total=30),
        )
        await self._load_cursor()

    async def close(self) -> None:
        """Close client: cleanup session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _build_params(self) -> dict:
        """Build API request parameters with origin filtering (ADR-015).

        Uses APIQuerySettings from Settings if provided, otherwise defaults.
        Parameters reduce data volume ~60-70% by filtering at API level.

        Returns:
            Dict of query parameters for API request.
        """
        q = self._api_query

        params = {
            "product": q.product if q else "surebets",
            "outcomes": str(q.outcomes if q else 2),
            "order": q.order if q else "created_at_desc",
            "min-profit": str(q.min_profit if q else -1),
            "max-profit": str(q.max_profit if q else 25),
            "min-odds": str(q.min_odds if q else 1.10),
            "max-odds": str(q.max_odds if q else 9.99),
            "hide-different-rules": str(q.hide_different_rules if q else True).lower(),
            "startAge": q.start_age if q else "PT10M",
            "oddsFormat": q.odds_format if q else "eu",
            "limit": str(q.limit if q else 5000),
            "source": "|".join(self._bookmakers),
            "sport": "|".join(self._sports),
        }

        if self._cursor.cursor_string:
            params["cursor"] = self._cursor.cursor_string

        return params

    async def fetch_picks(self) -> List[dict]:
        """Fetch picks from API with cursor pagination.

        Uses cursor from last call to get only new picks.
        Alias for fetch_surebets() using instance bookmakers/sports.

        Returns:
            List of new surebet records
        """
        return await self.fetch_surebets()

    async def fetch_surebets(
        self,
        bookmakers: Optional[List[str]] = None,
        sports: Optional[List[str]] = None,
    ) -> List[dict]:
        """Fetch surebets from API with cursor pagination (ADR-009).

        Args:
            bookmakers: Optional override for bookmaker list
            sports: Optional override for sports list

        Returns:
            List of surebet records from API
        """
        if self._session is None or self._session.closed:
            await self.initialize()

        # Build params, allowing overrides
        params = self._build_params()
        if bookmakers:
            params["source"] = "|".join(bookmakers)
        if sports:
            params["sport"] = "|".join(sports)

        try:
            async with self._session.get(self._url, params=params) as response:
                if response.status == 429:
                    # Rate limited - report to limiter
                    self._rate_limiter.on_rate_limit()
                    return []

                if response.status != 200:
                    return []

                data = await response.json()
                records = data.get("records", [])

                if records:
                    # Success - report to limiter and update cursor
                    self._rate_limiter.on_success()
                    await self._update_cursor(records)

                return records

        except aiohttp.ClientError:
            return []

    async def _update_cursor(self, picks: List[dict]) -> None:
        """Update cursor from last pick in response.

        Cursor format: {sort_by}:{id}
        Persists to Redis for recovery after restart.

        Args:
            picks: List of pick records from API response
        """
        if not picks:
            return

        last_pick = picks[-1]
        self._cursor = CursorState(
            sort_by=str(last_pick.get("sort_by", "created_at")),
            last_id=str(last_pick.get("id", "")),
        )

        if self._cursor_repo and self._cursor.cursor_string:
            await self._cursor_repo.set_cursor(self._cursor.cursor_string)

    async def _load_cursor(self) -> None:
        """Load persisted cursor from repository.

        Called on startup for recovery after restart.
        """
        if self._cursor_repo is None:
            return

        cursor_str = await self._cursor_repo.get_cursor()
        if cursor_str:
            self._cursor = CursorState.from_string(cursor_str)

    # === Test helper methods ===

    def get_cursor(self) -> Optional[str]:
        """Get current cursor string (for testing)."""
        return self._cursor.cursor_string

    def set_cursor(self, cursor: str) -> None:
        """Set cursor from string (for testing)."""
        self._cursor = CursorState.from_string(cursor)

    def reset_cursor(self) -> None:
        """Reset cursor to initial state (for testing)."""
        self._cursor = CursorState()
