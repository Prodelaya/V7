"""Unit tests for TelegramGateway.

Tests cover:
- PriorityMessage ordering
- Queue operations (enqueue, full queue, replacement)
- Bot rotation (round-robin)
- Processing lifecycle (start/stop)
- Send with retries and error handling
- Gateway close/cleanup
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.pick import Pick
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds
from src.infrastructure.messaging.telegram_gateway import (
    PriorityMessage,
    TelegramGateway,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_formatter():
    """Create a mock MessageFormatter."""
    formatter = MagicMock()
    formatter.format = AsyncMock(return_value="<b>Test message</b>")
    return formatter


@pytest.fixture
def sample_pick() -> Pick:
    """Create a sample Pick entity."""
    return Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.05),
        market_type=MarketType.OVER,
        variety="2.5",
        event_time=datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
        bookmaker="pinnaclesports",
        tournament="Premier League",
        sport_id="football",
    )


@pytest.fixture
def gateway(mock_formatter):
    """Create TelegramGateway with mocked bots."""
    with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
        mock_bot = MagicMock()
        mock_bot.token = "123456:ABC"
        mock_bot.send_message = AsyncMock(return_value=True)
        mock_bot.session = MagicMock()
        mock_bot.session.close = AsyncMock()
        MockBot.return_value = mock_bot

        gw = TelegramGateway(
            bot_tokens=["token1", "token2", "token3"],
            formatter=mock_formatter,
            max_retries=3,
        )
        return gw


@pytest.fixture
def gateway_single_bot(mock_formatter):
    """Create TelegramGateway with single bot."""
    with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
        mock_bot = MagicMock()
        mock_bot.token = "123456:ABC"
        mock_bot.send_message = AsyncMock(return_value=True)
        mock_bot.session = MagicMock()
        mock_bot.session.close = AsyncMock()
        MockBot.return_value = mock_bot

        return TelegramGateway(
            bot_tokens=["token1"],
            formatter=mock_formatter,
        )


# =============================================================================
# PriorityMessage Tests
# =============================================================================


class TestPriorityMessage:
    """Tests for PriorityMessage dataclass ordering."""

    def test_ordering_by_priority(self) -> None:
        """Lower priority value (higher profit) should come first."""
        msg_high = PriorityMessage(
            priority=-5.0,  # profit 5%
            timestamp=1.0,
            pick=None,
            channel_id=123,
            formatted="high",
        )
        msg_low = PriorityMessage(
            priority=-1.0,  # profit 1%
            timestamp=2.0,
            pick=None,
            channel_id=123,
            formatted="low",
        )

        # In a heap, msg_high should be "less than" msg_low (comes first)
        assert msg_high < msg_low

    def test_ordering_with_equal_priority_uses_timestamp(self) -> None:
        """Equal priorities should use timestamp as tie-breaker (FIFO)."""
        msg_earlier = PriorityMessage(
            priority=-2.0,
            timestamp=1.0,
            pick=None,
            channel_id=123,
            formatted="earlier",
        )
        msg_later = PriorityMessage(
            priority=-2.0,
            timestamp=2.0,
            pick=None,
            channel_id=123,
            formatted="later",
        )

        assert msg_earlier < msg_later

    def test_dataclass_fields(self) -> None:
        """All fields should be set correctly."""
        msg = PriorityMessage(
            priority=-3.5,
            timestamp=100.0,
            pick="test_pick",
            channel_id=456,
            formatted="<b>test</b>",
            retries=2,
        )

        assert msg.priority == -3.5
        assert msg.timestamp == 100.0
        assert msg.pick == "test_pick"
        assert msg.channel_id == 456
        assert msg.formatted == "<b>test</b>"
        assert msg.retries == 2


# =============================================================================
# TelegramGateway Init Tests
# =============================================================================


class TestTelegramGatewayInit:
    """Tests for TelegramGateway initialization."""

    def test_creates_bots_from_tokens(self, gateway: TelegramGateway) -> None:
        """Should create a bot for each token."""
        assert gateway.bot_count == 3

    def test_initial_queue_empty(self, gateway: TelegramGateway) -> None:
        """Queue should start empty."""
        assert gateway.queue_size == 0

    def test_initial_not_running(self, gateway: TelegramGateway) -> None:
        """Processing should not be running initially."""
        assert gateway.is_running is False

    def test_raises_on_empty_tokens(self, mock_formatter) -> None:
        """Should raise ValueError if no tokens provided."""
        with pytest.raises(ValueError, match="At least one bot token"):
            TelegramGateway(bot_tokens=[], formatter=mock_formatter)

    def test_custom_max_queue_size(self, mock_formatter) -> None:
        """Should accept custom max queue size."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot"):
            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=mock_formatter,
                max_queue_size=500,
            )
            assert gw._max_queue_size == 500


# =============================================================================
# Send Method Tests
# =============================================================================


class TestSendMethod:
    """Tests for the send() method."""

    @pytest.mark.asyncio
    async def test_send_adds_to_queue(
        self, gateway: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Send should add message to queue."""
        result = await gateway.send(sample_pick, channel_id=123, profit=2.5)

        assert result is True
        assert gateway.queue_size == 1

    @pytest.mark.asyncio
    async def test_send_with_pre_formatted_message(
        self, gateway: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Send should use pre-formatted message if provided."""
        result = await gateway.send(
            sample_pick,
            channel_id=123,
            profit=2.5,
            formatted_message="<b>Custom</b>",
        )

        assert result is True
        # Formatter should not be called
        gateway._formatter.format.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_rejects_empty_formatted(
        self, gateway: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Send should reject if formatter returns empty string."""
        gateway._formatter.format = AsyncMock(return_value="")

        result = await gateway.send(sample_pick, channel_id=123, profit=2.5)

        assert result is False
        assert gateway.queue_size == 0

    @pytest.mark.asyncio
    async def test_queue_maintains_priority_order(
        self, gateway: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Higher profit messages should have higher priority."""
        await gateway.send(sample_pick, 123, profit=1.0, formatted_message="low")
        await gateway.send(sample_pick, 123, profit=5.0, formatted_message="high")
        await gateway.send(sample_pick, 123, profit=3.0, formatted_message="mid")

        assert gateway.queue_size == 3
        # Min profit in queue should be 1.0
        assert gateway.get_min_profit_in_queue() == 1.0

    @pytest.mark.asyncio
    async def test_queue_full_rejects_low_priority(
        self, mock_formatter, sample_pick: Pick
    ) -> None:
        """Full queue should reject messages with lower priority than min."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot"):
            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=mock_formatter,
                max_queue_size=3,
            )

        # Fill queue with profits 2.0, 3.0, 4.0
        await gw.send(sample_pick, 123, profit=2.0, formatted_message="a")
        await gw.send(sample_pick, 123, profit=3.0, formatted_message="b")
        await gw.send(sample_pick, 123, profit=4.0, formatted_message="c")

        # Try to add profit 1.5 - should be rejected
        result = await gw.send(sample_pick, 123, profit=1.5, formatted_message="d")

        assert result is False
        assert gw.queue_size == 3

    @pytest.mark.asyncio
    async def test_queue_full_replaces_min_priority(
        self, mock_formatter, sample_pick: Pick
    ) -> None:
        """Full queue should replace min when new message has higher priority."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot"):
            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=mock_formatter,
                max_queue_size=3,
            )

        # Fill queue with profits 2.0, 3.0, 4.0
        await gw.send(sample_pick, 123, profit=2.0, formatted_message="a")
        await gw.send(sample_pick, 123, profit=3.0, formatted_message="b")
        await gw.send(sample_pick, 123, profit=4.0, formatted_message="c")

        # Add profit 5.0 - should replace 2.0
        result = await gw.send(sample_pick, 123, profit=5.0, formatted_message="e")

        assert result is True
        assert gw.queue_size == 3
        assert gw.get_min_profit_in_queue() == 3.0  # 2.0 was replaced


# =============================================================================
# Processing Lifecycle Tests
# =============================================================================


class TestProcessingLifecycle:
    """Tests for start/stop processing."""

    @pytest.mark.asyncio
    async def test_start_processing_sets_running(
        self, gateway: TelegramGateway
    ) -> None:
        """start_processing should set is_running to True."""
        await gateway.start_processing()

        assert gateway.is_running is True

        # Cleanup
        await gateway.stop_processing()

    @pytest.mark.asyncio
    async def test_start_processing_idempotent(
        self, gateway: TelegramGateway
    ) -> None:
        """Multiple start calls should be safe."""
        await gateway.start_processing()
        await gateway.start_processing()

        assert gateway.is_running is True

        await gateway.stop_processing()

    @pytest.mark.asyncio
    async def test_stop_processing_sets_not_running(
        self, gateway: TelegramGateway
    ) -> None:
        """stop_processing should set is_running to False."""
        await gateway.start_processing()
        await gateway.stop_processing()

        assert gateway.is_running is False

    @pytest.mark.asyncio
    async def test_stop_processing_when_not_started(
        self, gateway: TelegramGateway
    ) -> None:
        """stop_processing when not running should be safe."""
        await gateway.stop_processing()
        assert gateway.is_running is False


# =============================================================================
# Bot Rotation Tests
# =============================================================================


class TestBotRotation:
    """Tests for bot rotation."""

    def test_rotate_cycles_through_bots(self, gateway: TelegramGateway) -> None:
        """Rotation should cycle through all bots."""
        assert gateway._current_bot_index == 0

        gateway._rotate_bot()
        assert gateway._current_bot_index == 1

        gateway._rotate_bot()
        assert gateway._current_bot_index == 2

    def test_rotate_wraps_around(self, gateway: TelegramGateway) -> None:
        """Rotation should wrap to first bot after last."""
        gateway._current_bot_index = 2
        gateway._rotate_bot()

        assert gateway._current_bot_index == 0


# =============================================================================
# Send Message Tests
# =============================================================================


class TestSendMessage:
    """Tests for _send_message with error handling."""

    @pytest.mark.asyncio
    async def test_success_returns_true(self, gateway: TelegramGateway) -> None:
        """Successful send should return True."""
        message = PriorityMessage(
            priority=-2.0,
            timestamp=1.0,
            pick=None,
            channel_id=123,
            formatted="<b>Test</b>",
        )

        result = await gateway._send_message(message)

        assert result is True

    @pytest.mark.asyncio
    async def test_bad_request_returns_false(self, gateway: TelegramGateway) -> None:
        """TelegramBadRequest should return False (no retry)."""
        from aiogram.exceptions import TelegramBadRequest

        gateway._bots[0].send_message = AsyncMock(
            side_effect=TelegramBadRequest(method=MagicMock(), message="Bad format")
        )

        message = PriorityMessage(
            priority=-2.0,
            timestamp=1.0,
            pick=None,
            channel_id=123,
            formatted="<invalid>",
        )

        result = await gateway._send_message(message)

        assert result is False


# =============================================================================
# Close Tests
# =============================================================================


class TestClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_stops_processing(self, gateway: TelegramGateway) -> None:
        """Close should stop processing."""
        await gateway.start_processing()
        await gateway.close()

        assert gateway.is_running is False

    @pytest.mark.asyncio
    async def test_close_closes_all_sessions(self, gateway: TelegramGateway) -> None:
        """Close should close all bot sessions."""
        await gateway.close()

        # Each bot's session.close() should be called
        # Note: fixture uses shared mock, so we check it was called at least N times
        for bot in gateway._bots:
            bot.session.close.assert_called()


# =============================================================================
# Queue Properties Tests
# =============================================================================


class TestQueueProperties:
    """Tests for queue helper properties."""

    @pytest.mark.asyncio
    async def test_get_min_profit_empty_queue(
        self, gateway: TelegramGateway
    ) -> None:
        """get_min_profit_in_queue should return None for empty queue."""
        assert gateway.get_min_profit_in_queue() is None

    @pytest.mark.asyncio
    async def test_get_min_profit_with_items(
        self, gateway: TelegramGateway, sample_pick: Pick
    ) -> None:
        """get_min_profit_in_queue should return minimum profit."""
        await gateway.send(sample_pick, 123, profit=3.0, formatted_message="a")
        await gateway.send(sample_pick, 123, profit=1.0, formatted_message="b")
        await gateway.send(sample_pick, 123, profit=5.0, formatted_message="c")

        assert gateway.get_min_profit_in_queue() == 1.0
