"""Integration tests for API client.

These tests may make real API calls.
Use with caution and appropriate mocking.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.api.rate_limiter import AdaptiveRateLimiter
from src.infrastructure.api.surebet_client import CursorState, SurebetClient


class TestCursorState:
    """Tests for CursorState."""

    def test_cursor_string_with_id(self):
        """Test cursor string generation."""
        cursor = CursorState(sort_by="created_at", last_id="12345")

        assert cursor.cursor_string == "created_at:12345"

    def test_cursor_string_without_id(self):
        """Test cursor string is None without ID."""
        cursor = CursorState()

        assert cursor.cursor_string is None

    def test_from_string(self):
        """Test parsing cursor from string."""
        cursor = CursorState.from_string("created_at:12345")

        assert cursor.sort_by == "created_at"
        assert cursor.last_id == "12345"


class TestSurebetClient:
    """Tests for SurebetClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = AdaptiveRateLimiter()
        self.client = SurebetClient(
            api_url="https://api.example.com/request",
            api_token="test_token",
            rate_limiter=self.rate_limiter,
        )

    @pytest.mark.asyncio
    async def test_cursor_management(self):
        """Test cursor get/set/reset."""
        # Initially no cursor
        assert self.client.get_cursor() is None

        # Set cursor
        self.client.set_cursor("created_at:12345")
        assert self.client.get_cursor() == "created_at:12345"

        # Reset cursor
        self.client.reset_cursor()
        assert self.client.get_cursor() is None

    @pytest.mark.asyncio
    async def test_fetch_surebets_success(self):
        """Test successful API fetch with mocked response."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "records": [
                {"id": "1", "profit": 2.5},
                {"id": "2", "profit": 3.0},
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False

        self.client._session = mock_session

        records = await self.client.fetch_surebets(
            bookmakers=["pinnaclesports", "retabet"],
            sports=["Football"],
        )

        assert len(records) == 2
        assert self.client.get_cursor() == "created_at:2"  # Last ID

    @pytest.mark.asyncio
    async def test_fetch_surebets_rate_limited(self):
        """Test handling of 429 response."""
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "5"}
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False

        self.client._session = mock_session

        records = await self.client.fetch_surebets(
            bookmakers=["pinnaclesports"],
            sports=["Football"],
        )

        assert records == []
        assert self.rate_limiter.current_interval > 0.5  # Interval increased
