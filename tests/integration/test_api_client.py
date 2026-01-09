"""Integration tests for API client.

Comprehensive tests for SurebetClient covering:
- CursorState parsing and edge cases
- SurebetClient initialization and lifecycle
- API parameter building (ADR-015)
- Fetch operations with mocked responses
- Error handling (network, HTTP errors)
- Cursor persistence (ADR-009)
- Rate limiter integration (ADR-010)

Reference:
- docs/05-Implementation.md: Task 5B.3
- docs/03-ADRs.md: ADR-009, ADR-010, ADR-015
"""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from src.config.settings import APIQuerySettings
from src.infrastructure.api.rate_limiter import AdaptiveRateLimiter
from src.infrastructure.api.surebet_client import CursorState, SurebetClient

# ============================================================================
# TestCursorState - Cursor parsing and edge cases
# ============================================================================


class TestCursorState:
    """Tests for CursorState dataclass."""

    def test_cursor_string_with_id(self):
        """Test cursor string generation with valid ID."""
        cursor = CursorState(sort_by="created_at", last_id="12345")
        assert cursor.cursor_string == "created_at:12345"

    def test_cursor_string_without_id(self):
        """Test cursor string is None without ID."""
        cursor = CursorState()
        assert cursor.cursor_string is None

    def test_cursor_string_with_none_id(self):
        """Test cursor string is None when last_id is None."""
        cursor = CursorState(sort_by="created_at", last_id=None)
        assert cursor.cursor_string is None

    def test_from_string_standard_format(self):
        """Test parsing cursor from standard format."""
        cursor = CursorState.from_string("created_at:12345")
        assert cursor.sort_by == "created_at"
        assert cursor.last_id == "12345"

    def test_from_string_numeric_sort_by(self):
        """Test parsing cursor with numeric sort_by (API format)."""
        cursor = CursorState.from_string("4609118910833099900:785141488")
        assert cursor.sort_by == "4609118910833099900"
        assert cursor.last_id == "785141488"

    def test_from_string_multiple_colons(self):
        """Test parsing cursor with multiple colons keeps rest as ID."""
        cursor = CursorState.from_string("sort:id:with:colons")
        assert cursor.sort_by == "sort"
        assert cursor.last_id == "id:with:colons"

    def test_from_string_invalid_no_colon(self):
        """Test parsing invalid cursor returns defaults."""
        cursor = CursorState.from_string("invalid_no_colon")
        assert cursor.sort_by == "created_at"
        assert cursor.last_id is None

    def test_from_string_empty(self):
        """Test parsing empty string returns defaults."""
        cursor = CursorState.from_string("")
        assert cursor.sort_by == "created_at"
        assert cursor.last_id is None


# ============================================================================
# TestSurebetClientInitialization - Constructor and lifecycle
# ============================================================================


class TestSurebetClientInitialization:
    """Tests for SurebetClient initialization and lifecycle."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()

    def test_constructor_sets_defaults(self):
        """Test constructor with minimal params uses defaults."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )
        assert client._url == "https://api.example.com/request"
        assert client._token == "test_token"
        assert client._bookmakers == []
        assert client._sports == []
        assert client._timeout == 30
        assert client._session is None

    def test_constructor_with_all_params(self):
        """Test constructor with all parameters."""
        mock_repo = MagicMock()
        api_query = APIQuerySettings()

        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            cursor_repository=mock_repo,
            api_query=api_query,
            bookmakers=["pinnaclesports", "bet365"],
            sports=["Football", "Tennis"],
            timeout=60,
        )
        assert client._cursor_repo is mock_repo
        assert client._api_query is api_query
        assert client._bookmakers == ["pinnaclesports", "bet365"]
        assert client._sports == ["Football", "Tennis"]
        assert client._timeout == 60

    @pytest.mark.asyncio
    async def test_initialize_creates_session(self):
        """Test initialize() creates aiohttp session."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )
        await client.initialize()

        assert client._session is not None
        assert isinstance(client._session, aiohttp.ClientSession)

        await client.close()

    @pytest.mark.asyncio
    async def test_initialize_loads_cursor(self):
        """Test initialize() loads cursor from repository."""
        mock_repo = MagicMock()
        mock_repo.get_cursor = AsyncMock(return_value="created_at:999")

        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            cursor_repository=mock_repo,
        )
        await client.initialize()

        assert client.get_cursor() == "created_at:999"
        mock_repo.get_cursor.assert_called_once()

        await client.close()

    @pytest.mark.asyncio
    async def test_close_clears_session(self):
        """Test close() clears session."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )
        await client.initialize()
        assert client._session is not None

        await client.close()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        """Test multiple close() calls are safe."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )
        # Close without initialize should not raise
        await client.close()
        await client.close()
        assert client._session is None


# ============================================================================
# TestSurebetClientBuildParams - API parameter building (ADR-015)
# ============================================================================


class TestSurebetClientBuildParams:
    """Tests for _build_params() method (ADR-015 compliance)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()

    def test_build_params_without_api_query(self):
        """Test _build_params uses defaults without APIQuerySettings."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            bookmakers=["bk1"],
            sports=["Football"],
        )
        params = client._build_params()

        assert params["product"] == "surebets"
        assert params["outcomes"] == "2"
        assert params["order"] == "created_at_desc"
        assert params["min-profit"] == "-1"
        assert params["max-profit"] == "25"
        assert params["min-odds"] == "1.1"
        assert params["max-odds"] == "9.99"
        assert params["hide-different-rules"] == "true"
        assert params["startAge"] == "PT10M"
        assert params["oddsFormat"] == "eu"
        assert params["limit"] == "5000"

    def test_build_params_with_api_query(self):
        """Test _build_params uses APIQuerySettings values."""
        api_query = APIQuerySettings(
            min_profit=0.5,
            max_profit=15.0,
            min_odds=1.50,
            max_odds=5.00,
            limit=1000,
        )
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            api_query=api_query,
            bookmakers=["bk1"],
            sports=["Football"],
        )
        params = client._build_params()

        assert params["min-profit"] == "0.5"
        assert params["max-profit"] == "15.0"
        assert params["min-odds"] == "1.5"
        assert params["max-odds"] == "5.0"
        assert params["limit"] == "1000"

    def test_build_params_includes_cursor_when_set(self):
        """Test cursor parameter included when cursor is set."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )
        client.set_cursor("created_at:12345")
        params = client._build_params()

        assert params["cursor"] == "created_at:12345"

    def test_build_params_no_cursor_initially(self):
        """Test no cursor parameter on initial request."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )
        params = client._build_params()

        assert "cursor" not in params

    def test_build_params_bookmakers_joined(self):
        """Test bookmakers joined with pipe separator."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            bookmakers=["pinnaclesports", "bet365", "retabet"],
        )
        params = client._build_params()

        assert params["source"] == "pinnaclesports|bet365|retabet"

    def test_build_params_sports_joined(self):
        """Test sports joined with pipe separator."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            sports=["Football", "Tennis", "Basketball"],
        )
        params = client._build_params()

        assert params["sport"] == "Football|Tennis|Basketball"


# ============================================================================
# TestSurebetClientCursorManagement - Cursor get/set/reset
# ============================================================================


class TestSurebetClientCursorManagement:
    """Tests for cursor management helpers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()
        self.client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )

    def test_cursor_management(self):
        """Test cursor get/set/reset."""
        # Initially no cursor
        assert self.client.get_cursor() is None

        # Set cursor
        self.client.set_cursor("created_at:12345")
        assert self.client.get_cursor() == "created_at:12345"

        # Reset cursor
        self.client.reset_cursor()
        assert self.client.get_cursor() is None


# ============================================================================
# TestSurebetClientFetch - Fetch operations with mocked responses
# ============================================================================


class TestSurebetClientFetch:
    """Tests for fetch operations with mocked HTTP responses."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()
        self.client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )

    def _mock_response(self, status: int, json_data: dict = None):
        """Create a mock aiohttp response."""
        mock_response = MagicMock()
        mock_response.status = status
        mock_response.json = AsyncMock(return_value=json_data or {})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        return mock_response

    def _mock_session(self, response):
        """Create a mock aiohttp session."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=response)
        mock_session.closed = False
        return mock_session

    @pytest.mark.asyncio
    async def test_fetch_surebets_success(self):
        """Test successful API fetch with mocked response."""
        response = self._mock_response(200, {
            "records": [
                {"id": "1", "sort_by": "created_at", "profit": 2.5},
                {"id": "2", "sort_by": "created_at", "profit": 3.0},
            ]
        })
        self.client._session = self._mock_session(response)

        records = await self.client.fetch_surebets(
            bookmakers=["pinnaclesports", "retabet"],
            sports=["Football"],
        )

        assert len(records) == 2
        assert self.client.get_cursor() == "created_at:2"

    @pytest.mark.asyncio
    async def test_fetch_surebets_rate_limited(self):
        """Test handling of 429 response."""
        response = self._mock_response(429)
        self.client._session = self._mock_session(response)

        records = await self.client.fetch_surebets(
            bookmakers=["pinnaclesports"],
            sports=["Football"],
        )

        assert records == []
        assert self.rate_limiter.current_interval > 0.5  # Interval increased

    @pytest.mark.asyncio
    async def test_fetch_surebets_empty_records(self):
        """Test fetch with empty records doesn't update cursor."""
        self.client.set_cursor("old:cursor")
        response = self._mock_response(200, {"records": []})
        self.client._session = self._mock_session(response)

        records = await self.client.fetch_surebets()

        assert records == []
        assert self.client.get_cursor() == "old:cursor"  # Unchanged

    @pytest.mark.asyncio
    async def test_fetch_surebets_with_overrides(self):
        """Test fetch with bookmaker/sport overrides."""
        response = self._mock_response(200, {"records": []})
        mock_session = self._mock_session(response)
        self.client._session = mock_session

        await self.client.fetch_surebets(
            bookmakers=["override_bk"],
            sports=["Override_Sport"],
        )

        # Verify the session.get was called
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params["source"] == "override_bk"
        assert params["sport"] == "Override_Sport"

    @pytest.mark.asyncio
    async def test_fetch_picks_alias(self):
        """Test fetch_picks() is an alias for fetch_surebets()."""
        response = self._mock_response(200, {
            "records": [{"id": "1", "sort_by": "created_at"}]
        })
        self.client._session = self._mock_session(response)

        records = await self.client.fetch_picks()

        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_fetch_auto_initializes_session(self):
        """Test fetch auto-initializes closed session."""
        # Session is None initially
        assert self.client._session is None

        with patch.object(self.client, "initialize", new_callable=AsyncMock) as mock_init:
            # Mock the session after "initialize" is called
            response = self._mock_response(200, {"records": []})

            async def set_session():
                self.client._session = self._mock_session(response)

            mock_init.side_effect = set_session

            await self.client.fetch_surebets()

            mock_init.assert_called_once()


# ============================================================================
# TestSurebetClientErrorHandling - Error scenarios
# ============================================================================


class TestSurebetClientErrorHandling:
    """Tests for error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()
        self.client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )

    @pytest.mark.asyncio
    async def test_fetch_non_200_returns_empty(self):
        """Test non-200 responses return empty list."""
        for status in [400, 401, 403, 500, 502, 503]:
            mock_response = MagicMock()
            mock_response.status = status
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.closed = False
            self.client._session = mock_session

            records = await self.client.fetch_surebets()
            assert records == [], f"Status {status} should return empty list"

    @pytest.mark.asyncio
    async def test_fetch_network_error_returns_empty(self):
        """Test network errors return empty list."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Network error"))
        mock_session.closed = False
        self.client._session = mock_session

        records = await self.client.fetch_surebets()
        assert records == []


# ============================================================================
# TestSurebetClientCursorPersistence - Repository integration (ADR-009)
# ============================================================================


class TestSurebetClientCursorPersistence:
    """Tests for cursor persistence with repository (ADR-009)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()
        self.mock_repo = MagicMock()
        self.mock_repo.get_cursor = AsyncMock(return_value=None)
        self.mock_repo.set_cursor = AsyncMock(return_value=True)

    @pytest.mark.asyncio
    async def test_cursor_loaded_from_repository(self):
        """Test cursor loaded from repository on initialize."""
        self.mock_repo.get_cursor = AsyncMock(return_value="persisted:cursor")
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            cursor_repository=self.mock_repo,
        )

        await client.initialize()
        assert client.get_cursor() == "persisted:cursor"
        await client.close()

    @pytest.mark.asyncio
    async def test_cursor_persisted_on_fetch(self):
        """Test cursor persisted to repository after successful fetch."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            cursor_repository=self.mock_repo,
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "records": [{"id": "999", "sort_by": "created_at"}]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        client._session = mock_session

        await client.fetch_surebets()

        self.mock_repo.set_cursor.assert_called_once_with("created_at:999")

    @pytest.mark.asyncio
    async def test_cursor_not_persisted_without_repository(self):
        """Test cursor not persisted when no repository configured."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            # No cursor_repository
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "records": [{"id": "999", "sort_by": "created_at"}]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        client._session = mock_session

        # Should not raise even without repository
        await client.fetch_surebets()
        assert client.get_cursor() == "created_at:999"

    @pytest.mark.asyncio
    async def test_cursor_not_persisted_on_empty_response(self):
        """Test cursor not persisted when response has no records."""
        client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
            cursor_repository=self.mock_repo,
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"records": []})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        client._session = mock_session

        await client.fetch_surebets()

        self.mock_repo.set_cursor.assert_not_called()


# ============================================================================
# TestSurebetClientRateLimiterIntegration - ADR-010 compliance
# ============================================================================


class TestSurebetClientRateLimiterIntegration:
    """Tests for AdaptiveRateLimiter integration (ADR-010)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()
        self.client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )

    @pytest.mark.asyncio
    async def test_on_success_called_on_records(self):
        """Test rate limiter on_success called when records received."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "records": [{"id": "1", "sort_by": "created_at"}]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        self.client._session = mock_session

        # Pre-set consecutive_429 to test recovery
        self.rate_limiter._consecutive_429 = 2
        initial_interval = self.rate_limiter.current_interval

        await self.client.fetch_surebets()

        # Interval should decrease after success
        assert self.rate_limiter.current_interval < initial_interval

    @pytest.mark.asyncio
    async def test_on_rate_limit_called_on_429(self):
        """Test rate limiter on_rate_limit called on 429 response."""
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        self.client._session = mock_session

        initial_interval = self.rate_limiter.current_interval  # 0.5

        await self.client.fetch_surebets()

        # Interval should increase after 429
        assert self.rate_limiter.current_interval > initial_interval

    @pytest.mark.asyncio
    async def test_rate_limiter_interval_increases_exponentially(self):
        """Test rate limiter interval increases exponentially on 429s."""
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        self.client._session = mock_session

        intervals = []
        for _ in range(4):
            await self.client.fetch_surebets()
            intervals.append(self.rate_limiter.current_interval)

        # Intervals: 1.0, 2.0, 4.0, 5.0 (capped at max)
        assert intervals == [1.0, 2.0, 4.0, 5.0]
