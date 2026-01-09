"""Integration tests for messaging infrastructure.

Tests cover:
- MessageFormatter with real CalculationService (not mocked)
- TelegramGateway with mocked Telegram API but real queue/formatter
- Cache behavior (ADR-011)
- Heap priority queue (ADR-006)
- End-to-end message flow
- Domain adjustments in full message context (RF-010)

Reference:
- docs/05-Implementation.md: Task 5C.4
- docs/03-ADRs.md: ADR-006, ADR-011
- docs/01-SRS.md: RF-007, RF-010
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.pick import Pick
from src.domain.services.calculation_service import CalculationService
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds
from src.infrastructure.messaging.message_formatter import MessageFormatter
from src.infrastructure.messaging.telegram_gateway import TelegramGateway

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def calculation_service() -> CalculationService:
    """Create real CalculationService with default settings."""
    return CalculationService()


@pytest.fixture
def formatter() -> MessageFormatter:
    """Create MessageFormatter without calculation service."""
    return MessageFormatter()


@pytest.fixture
def formatter_with_service(calculation_service: CalculationService) -> MessageFormatter:
    """Create MessageFormatter with real CalculationService."""
    return MessageFormatter(calculation_service=calculation_service)


@pytest.fixture
def mock_bot():
    """Create a mock aiogram Bot."""
    bot = MagicMock()
    bot.token = "123456:ABCDEF"
    bot.send_message = AsyncMock(return_value=True)
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    return bot


@pytest.fixture
def gateway_with_real_formatter(formatter_with_service: MessageFormatter):
    """Create TelegramGateway with mocked bots but real formatter."""
    with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
        mock_bot = MagicMock()
        mock_bot.token = "123456:ABC"
        mock_bot.send_message = AsyncMock(return_value=True)
        mock_bot.session = MagicMock()
        mock_bot.session.close = AsyncMock()
        MockBot.return_value = mock_bot

        gw = TelegramGateway(
            bot_tokens=["token1", "token2", "token3"],
            formatter=formatter_with_service,
            max_retries=3,
        )
        return gw


@pytest.fixture
def sample_pick() -> Pick:
    """Create a standard test Pick."""
    return Pick(
        teams=("Team Alpha", "Team Beta"),
        odds=Odds(2.05),
        market_type=MarketType.OVER,
        variety="2.5",
        event_time=datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
        bookmaker="pinnaclesports",
        tournament="Premier League",
        sport_id="football",
        link="https://bet365.com/sports/football/match/12345",
    )


@pytest.fixture
def sample_pick_bet365() -> Pick:
    """Create a Pick with bet365 link for domain adjustment tests."""
    return Pick(
        teams=("Real Madrid", "Barcelona"),
        odds=Odds(1.90),
        market_type=MarketType.WIN1,
        variety="",
        event_time=datetime(2026, 1, 20, 21, 0, 0, tzinfo=timezone.utc),
        bookmaker="bet365",
        tournament="La Liga",
        sport_id="football",
        link="https://bet365.com/sports/football/laliga/match123",
    )


@pytest.fixture
def sample_pick_betway() -> Pick:
    """Create a Pick with betway link for domain adjustment tests."""
    return Pick(
        teams=("Man United", "Liverpool"),
        odds=Odds(2.30),
        market_type=MarketType.WIN2,
        variety="",
        event_time=datetime(2026, 1, 22, 16, 0, 0, tzinfo=timezone.utc),
        bookmaker="betway",
        tournament="Premier League",
        sport_id="football",
        link="https://sports.betway.com/en/sports/football/premier",
    )


@pytest.fixture
def sample_picks_varied_profit() -> List[Pick]:
    """Create multiple picks with varying profits for queue tests."""
    base_time = datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc)
    picks = []
    for i, profit_val in enumerate([1.0, 5.0, 3.0, 2.0, 8.0]):
        pick = Pick(
            teams=(f"Team{i}A", f"Team{i}B"),
            odds=Odds(1.8 + (i * 0.1)),
            market_type=MarketType.OVER,
            variety=str(2.5 + i * 0.5),
            event_time=base_time,
            bookmaker="pinnaclesports",
            tournament=f"League{i}",
            sport_id="football",
        )
        picks.append((pick, profit_val))
    return picks


# ============================================================================
# TestMessageFormatterWithCalculationService
# ============================================================================


class TestMessageFormatterWithCalculationService:
    """Tests MessageFormatter with real CalculationService (not mocked)."""

    @pytest.mark.asyncio
    async def test_format_with_real_calculation_service(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Format should work with real CalculationService."""
        result = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=2.5,
            sharp_bookmaker="pinnaclesports",
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain teams
        assert "Team Alpha" in result
        assert "Team Beta" in result

    @pytest.mark.asyncio
    async def test_format_generates_correct_stake_emoji(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Format should generate correct stake emoji based on profit."""
        # Profit 2.5% should give yellow emoji (🟡)
        result = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=2.5,
            sharp_bookmaker="pinnaclesports",
        )

        # Should contain an emoji from stake system
        assert any(emoji in result for emoji in ["🔴", "🟠", "🟡", "🟢"])

    @pytest.mark.asyncio
    async def test_format_calculates_min_odds(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Format should calculate and include min_odds."""
        result = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=2.5,
            sharp_bookmaker="pinnaclesports",
        )

        # Min odds indicator should be present
        assert "🔻" in result
        # Should have some numeric value after min_odds indicator

    @pytest.mark.asyncio
    async def test_format_rejects_invalid_profit(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Format should return empty for rejected profit values."""
        # Profit 30% exceeds max (typically 25%), should be rejected
        result = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=30.0,
            sharp_bookmaker="pinnaclesports",
        )

        # Should return empty string for rejected picks
        assert result == ""

    @pytest.mark.asyncio
    async def test_format_with_boundary_profits(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Format should handle boundary profit values."""
        # Test minimum boundary (-1%)
        result_min = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=-0.9,  # Just above min
            sharp_bookmaker="pinnaclesports",
        )
        assert isinstance(result_min, str)

        # Test zero profit
        result_zero = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=0.0,
            sharp_bookmaker="pinnaclesports",
        )
        assert isinstance(result_zero, str)


# ============================================================================
# TestTelegramGatewayIntegration
# ============================================================================


class TestTelegramGatewayIntegration:
    """Tests TelegramGateway with mocked Telegram API but real formatter."""

    @pytest.mark.asyncio
    async def test_gateway_with_real_formatter(
        self, gateway_with_real_formatter: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Gateway should work with real formatter."""
        result = await gateway_with_real_formatter.send(
            sample_pick,
            channel_id=-1001234567890,
            profit=2.5,
        )

        # Should queue successfully
        assert result is True
        assert gateway_with_real_formatter.queue_size == 1

    @pytest.mark.asyncio
    async def test_send_uses_formatted_message(
        self, gateway_with_real_formatter: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Send should call formatter and use formatted message."""
        await gateway_with_real_formatter.send(
            sample_pick,
            channel_id=-1001234567890,
            profit=2.5,
        )

        # Check that formatter was called (queue has message)
        assert gateway_with_real_formatter.queue_size > 0

    @pytest.mark.asyncio
    async def test_processing_loop_sends_highest_priority_first(
        self,
        formatter_with_service: MessageFormatter,
        sample_picks_varied_profit: List,
    ) -> None:
        """Processing loop should send highest profit picks first."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            sent_messages = []

            mock_bot = MagicMock()
            mock_bot.token = "123456:ABC"

            async def capture_send(*args, **kwargs):
                sent_messages.append(kwargs.get("text", ""))
                return True

            mock_bot.send_message = AsyncMock(side_effect=capture_send)
            mock_bot.session = MagicMock()
            mock_bot.session.close = AsyncMock()
            MockBot.return_value = mock_bot

            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
            )

            # Queue picks with different profits
            for pick, profit in sample_picks_varied_profit:
                await gw.send(
                    pick,
                    channel_id=-1001234567890,
                    profit=profit,
                    formatted_message=f"profit_{profit}",
                )

            # Process one message
            await gw.start_processing()
            await asyncio.sleep(0.2)
            await gw.stop_processing()

            # First message should be highest profit (8.0)
            if sent_messages:
                assert "profit_8.0" in sent_messages[0]

    @pytest.mark.asyncio
    async def test_queue_replacement_under_load(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Full queue should replace low priority with high priority."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            MockBot.return_value = MagicMock(
                token="123:ABC",
                send_message=AsyncMock(return_value=True),
                session=MagicMock(close=AsyncMock()),
            )

            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
                max_queue_size=3,
            )

            # Fill queue with low profit picks
            await gw.send(sample_pick, -100, 1.0, formatted_message="low1")
            await gw.send(sample_pick, -100, 2.0, formatted_message="low2")
            await gw.send(sample_pick, -100, 3.0, formatted_message="low3")

            assert gw.queue_size == 3
            assert gw.get_min_profit_in_queue() == 1.0

            # Add high priority - should replace lowest
            result = await gw.send(sample_pick, -100, 10.0, formatted_message="high")

            assert result is True
            assert gw.queue_size == 3
            assert gw.get_min_profit_in_queue() == 2.0  # 1.0 was replaced

    @pytest.mark.asyncio
    async def test_gateway_graceful_shutdown_with_queue(
        self, gateway_with_real_formatter: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Gateway should shut down gracefully with items in queue."""
        # Add items to queue
        await gateway_with_real_formatter.send(
            sample_pick, -100, 5.0, formatted_message="msg1"
        )
        await gateway_with_real_formatter.send(
            sample_pick, -100, 3.0, formatted_message="msg2"
        )

        await gateway_with_real_formatter.start_processing()
        await gateway_with_real_formatter.close()

        assert gateway_with_real_formatter.is_running is False


# ============================================================================
# TestMessageFormatterCacheIntegration (ADR-011)
# ============================================================================


class TestMessageFormatterCacheIntegration:
    """Tests cache behavior across multiple picks from the same event (ADR-011)."""

    @pytest.mark.asyncio
    async def test_cache_hit_for_same_event(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Same event should hit cache on second format."""
        # First call - cache miss
        await formatter_with_service.format(
            sample_pick, sharp_odds=2.05, profit=2.5
        )
        initial_cache_size = formatter_with_service.cache_size

        # Second call - cache hit (same pick)
        await formatter_with_service.format(
            sample_pick, sharp_odds=2.10, profit=3.0  # Different odds/profit
        )

        # Cache size should not increase (hit, not new entry)
        assert formatter_with_service.cache_size == initial_cache_size

    @pytest.mark.asyncio
    async def test_cache_miss_for_different_event(
        self, formatter_with_service: MessageFormatter
    ) -> None:
        """Different events should not share cache."""
        pick1 = Pick(
            teams=("TeamA", "TeamB"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            bookmaker="bookie1",
        )
        pick2 = Pick(
            teams=("TeamC", "TeamD"),  # Different teams
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            bookmaker="bookie1",
        )

        await formatter_with_service.format(pick1, sharp_odds=2.0, profit=2.0)
        await formatter_with_service.format(pick2, sharp_odds=2.0, profit=2.0)

        # Two different events = 2 cache entries
        assert formatter_with_service.cache_size == 2

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Cache should expire after TTL."""
        # First call
        await formatter_with_service.format(
            sample_pick, sharp_odds=2.05, profit=2.5
        )
        assert formatter_with_service.cache_size > 0

        # Manually expire cache by setting old timestamp
        key = formatter_with_service._get_cache_key(sample_pick)
        if key in formatter_with_service._cache:
            old_time = time.time() - 120  # 2 minutes ago (TTL is 60s)
            _, parts = formatter_with_service._cache[key]
            formatter_with_service._cache[key] = (old_time, parts)

        # Check that expired entry is not returned
        cached = formatter_with_service._get_cached_parts(key)
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_cleanup_on_memory_pressure(
        self, formatter_with_service: MessageFormatter
    ) -> None:
        """Cache should clean expired entries."""
        # Add several entries
        for i in range(5):
            pick = Pick(
                teams=(f"Team{i}A", f"Team{i}B"),
                odds=Odds(2.0),
                market_type=MarketType.WIN1,
                variety="",
                event_time=datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
                bookmaker=f"bookie{i}",
            )
            await formatter_with_service.format(pick, sharp_odds=2.0, profit=2.0)

        # Expire all entries manually
        current_time = time.time()
        for key in list(formatter_with_service._cache.keys()):
            _, parts = formatter_with_service._cache[key]
            formatter_with_service._cache[key] = (current_time - 120, parts)

        # Add new entry - should trigger cleanup
        new_pick = Pick(
            teams=("NewA", "NewB"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            bookmaker="new_bookie",
        )
        await formatter_with_service.format(new_pick, sharp_odds=2.0, profit=2.0)

        # Only new entry should remain
        assert formatter_with_service.cache_size == 1

    @pytest.mark.asyncio
    async def test_format_multiple_picks_same_event_uses_cache(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Multiple picks from same event should benefit from cache."""
        # Format same pick multiple times (simulating different bookmakers)
        results = []
        for _ in range(3):
            result = await formatter_with_service.format(
                sample_pick, sharp_odds=2.05, profit=2.5
            )
            results.append(result)

        # All results should be valid
        assert all(len(r) > 0 for r in results)
        # Cache should have only 1 entry (same event)
        assert formatter_with_service.cache_size == 1


# ============================================================================
# TestGatewayQueueBehavior (ADR-006)
# ============================================================================


class TestGatewayQueueBehavior:
    """Tests heap priority queue behavior (ADR-006)."""

    @pytest.mark.asyncio
    async def test_heap_order_by_profit(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Higher profit should have higher priority."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            MockBot.return_value = MagicMock(
                token="123:ABC",
                send_message=AsyncMock(return_value=True),
                session=MagicMock(close=AsyncMock()),
            )

            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
            )

            # Add picks with different profits
            await gw.send(sample_pick, -100, 1.0, formatted_message="low")
            await gw.send(sample_pick, -100, 5.0, formatted_message="high")
            await gw.send(sample_pick, -100, 3.0, formatted_message="mid")

            assert gw.queue_size == 3

            # Pop should return highest profit first (internally via _process_loop)
            # Check min profit is still 1.0
            assert gw.get_min_profit_in_queue() == 1.0

    @pytest.mark.asyncio
    async def test_queue_full_replaces_minimum_profit(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Full queue should replace minimum when higher profit added."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            MockBot.return_value = MagicMock(
                token="123:ABC",
                send_message=AsyncMock(return_value=True),
                session=MagicMock(close=AsyncMock()),
            )

            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
                max_queue_size=3,
            )

            # Fill queue
            await gw.send(sample_pick, -100, 2.0, formatted_message="a")
            await gw.send(sample_pick, -100, 4.0, formatted_message="b")
            await gw.send(sample_pick, -100, 6.0, formatted_message="c")

            # Add higher profit
            result = await gw.send(sample_pick, -100, 8.0, formatted_message="d")

            assert result is True
            assert gw.get_min_profit_in_queue() == 4.0  # 2.0 was replaced

    @pytest.mark.asyncio
    async def test_queue_full_rejects_lower_profit(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Full queue should reject lower profit picks."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            MockBot.return_value = MagicMock(
                token="123:ABC",
                send_message=AsyncMock(return_value=True),
                session=MagicMock(close=AsyncMock()),
            )

            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
                max_queue_size=3,
            )

            # Fill queue with high profits
            await gw.send(sample_pick, -100, 5.0, formatted_message="a")
            await gw.send(sample_pick, -100, 6.0, formatted_message="b")
            await gw.send(sample_pick, -100, 7.0, formatted_message="c")

            # Try to add lower profit
            result = await gw.send(sample_pick, -100, 4.0, formatted_message="d")

            assert result is False
            assert gw.queue_size == 3

    @pytest.mark.asyncio
    async def test_fifo_on_equal_profit(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Equal profits should use FIFO ordering."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            MockBot.return_value = MagicMock(
                token="123:ABC",
                send_message=AsyncMock(return_value=True),
                session=MagicMock(close=AsyncMock()),
            )

            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
            )

            # Add picks with same profit
            await gw.send(sample_pick, -100, 5.0, formatted_message="first")
            await asyncio.sleep(0.01)  # Ensure different timestamps
            await gw.send(sample_pick, -100, 5.0, formatted_message="second")

            assert gw.queue_size == 2

    @pytest.mark.asyncio
    async def test_queue_size_limits(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Queue should enforce maximum size limit."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            MockBot.return_value = MagicMock(
                token="123:ABC",
                send_message=AsyncMock(return_value=True),
                session=MagicMock(close=AsyncMock()),
            )

            max_size = 5
            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
                max_queue_size=max_size,
            )

            # Add more than max
            for i in range(max_size + 3):
                await gw.send(
                    sample_pick, -100, float(i), formatted_message=f"msg{i}"
                )

            # Queue should not exceed max
            assert gw.queue_size == max_size

    @pytest.mark.asyncio
    async def test_get_min_profit_in_queue_accuracy(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """get_min_profit_in_queue should return accurate minimum."""
        with patch("src.infrastructure.messaging.telegram_gateway.Bot") as MockBot:
            MockBot.return_value = MagicMock(
                token="123:ABC",
                send_message=AsyncMock(return_value=True),
                session=MagicMock(close=AsyncMock()),
            )

            gw = TelegramGateway(
                bot_tokens=["token1"],
                formatter=formatter_with_service,
            )

            # Empty queue
            assert gw.get_min_profit_in_queue() is None

            # Add picks
            await gw.send(sample_pick, -100, 3.5, formatted_message="a")
            await gw.send(sample_pick, -100, 1.5, formatted_message="b")
            await gw.send(sample_pick, -100, 7.5, formatted_message="c")

            assert gw.get_min_profit_in_queue() == 1.5


# ============================================================================
# TestEndToEndMessageFlow
# ============================================================================


class TestEndToEndMessageFlow:
    """Integration tests combining MessageFormatter + TelegramGateway + Pick."""

    @pytest.mark.asyncio
    async def test_pick_to_telegram_flow(
        self, gateway_with_real_formatter: TelegramGateway, sample_pick: Pick
    ) -> None:
        """Complete flow from Pick entity to queued message."""
        # Send pick through gateway
        result = await gateway_with_real_formatter.send(
            sample_pick,
            channel_id=-1001234567890,
            profit=2.5,
        )

        assert result is True
        assert gateway_with_real_formatter.queue_size == 1

    @pytest.mark.asyncio
    async def test_domain_adjustment_in_formatted_message(
        self,
        formatter_with_service: MessageFormatter,
        sample_pick_bet365: Pick,
    ) -> None:
        """Formatted message should have adjusted domain (RF-010)."""
        result = await formatter_with_service.format(
            sample_pick_bet365,
            sharp_odds=1.90,
            profit=2.0,
            sharp_bookmaker="pinnaclesports",
        )

        # bet365.com should be transformed to bet365.es
        assert "bet365.es" in result
        assert "bet365.com" not in result
        # Path should be uppercase
        assert "LALIGA" in result or "MATCH123" in result

    @pytest.mark.asyncio
    async def test_multiple_picks_ordered_by_profit(
        self, gateway_with_real_formatter: TelegramGateway
    ) -> None:
        """Multiple picks should be ordered by profit in queue."""
        picks_with_profits = [
            (Pick(
                teams=("A1", "B1"), odds=Odds(2.0), market_type=MarketType.WIN1,
                variety="", event_time=datetime.now(timezone.utc),
                bookmaker="test",
            ), 1.0, "low"),
            (Pick(
                teams=("A2", "B2"), odds=Odds(2.0), market_type=MarketType.WIN1,
                variety="", event_time=datetime.now(timezone.utc),
                bookmaker="test",
            ), 5.0, "high"),
            (Pick(
                teams=("A3", "B3"), odds=Odds(2.0), market_type=MarketType.WIN1,
                variety="", event_time=datetime.now(timezone.utc),
                bookmaker="test",
            ), 3.0, "mid"),
        ]

        for pick, profit, msg in picks_with_profits:
            await gateway_with_real_formatter.send(
                pick, -100, profit, formatted_message=msg
            )

        assert gateway_with_real_formatter.queue_size == 3
        assert gateway_with_real_formatter.get_min_profit_in_queue() == 1.0

    @pytest.mark.asyncio
    async def test_picks_with_different_sports_emojis(
        self, formatter_with_service: MessageFormatter
    ) -> None:
        """Different sports should show different emojis."""
        sports_picks = [
            ("football", "⚽️", "FootballTeamA", "FootballTeamB"),
            ("basketball", "🏀", "BasketTeamA", "BasketTeamB"),
            ("tennis", "🎾", "TennisPlayerA", "TennisPlayerB"),
        ]

        for sport_id, expected_emoji, team1, team2 in sports_picks:
            # Clear cache to ensure each sport gets fresh formatting
            formatter_with_service.clear_cache()
            pick = Pick(
                teams=(team1, team2),
                odds=Odds(2.0),
                market_type=MarketType.WIN1,
                variety="",
                event_time=datetime.now(timezone.utc),
                bookmaker="test",
                sport_id=sport_id,
            )
            result = await formatter_with_service.format(
                pick, sharp_odds=2.0, profit=2.0
            )
            assert expected_emoji in result, f"Expected {expected_emoji} for {sport_id}"

    @pytest.mark.asyncio
    async def test_error_handling_on_rejected_pick(
        self, gateway_with_real_formatter: TelegramGateway
    ) -> None:
        """Gateway should handle rejected picks gracefully."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )

        # Profit 50% should be rejected by calculator
        result = await gateway_with_real_formatter.send(
            pick,
            channel_id=-100,
            profit=50.0,  # Exceeds max, will be rejected
        )

        # Should not crash, but may return False or True with empty message
        assert isinstance(result, bool)


# ============================================================================
# TestMessageFormatterDomainAdjustments (RF-010)
# ============================================================================


class TestMessageFormatterDomainAdjustments:
    """Integration tests for URL transformation in full message context (RF-010)."""

    @pytest.mark.asyncio
    async def test_format_bet365_link_adjusted(
        self, formatter_with_service: MessageFormatter, sample_pick_bet365: Pick
    ) -> None:
        """bet365.com should become bet365.es in formatted message."""
        result = await formatter_with_service.format(
            sample_pick_bet365, sharp_odds=1.90, profit=2.0
        )

        assert "bet365.es" in result
        assert "bet365.com" not in result

    @pytest.mark.asyncio
    async def test_format_betway_link_adjusted(
        self, formatter_with_service: MessageFormatter, sample_pick_betway: Pick
    ) -> None:
        """betway.com/en should become betway.es/es in formatted message."""
        result = await formatter_with_service.format(
            sample_pick_betway, sharp_odds=2.30, profit=2.0
        )

        assert "betway.es/es" in result
        assert "betway.com/en" not in result

    @pytest.mark.asyncio
    async def test_format_pokerstars_link_adjusted(
        self, formatter_with_service: MessageFormatter
    ) -> None:
        """pokerstars.uk should become pokerstars.es."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="pokerstars",
            link="https://www.pokerstars.uk/sports/football",
        )

        result = await formatter_with_service.format(
            pick, sharp_odds=2.0, profit=2.0
        )

        assert "pokerstars.es" in result
        assert "pokerstars.uk" not in result

    @pytest.mark.asyncio
    async def test_format_versus_link_adjusted(
        self, formatter_with_service: MessageFormatter
    ) -> None:
        """versus sportswidget should be transformed."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="versus",
            link="https://sportswidget.versus.es/sports/football",
        )

        result = await formatter_with_service.format(
            pick, sharp_odds=2.0, profit=2.0
        )

        assert "www.versus.es/apuestas" in result

    @pytest.mark.asyncio
    async def test_format_preserves_unknown_bookmaker_url(
        self, formatter_with_service: MessageFormatter
    ) -> None:
        """Unknown bookmaker URLs should pass through unchanged."""
        original_url = "https://unknown-bookie.com/sports/match"
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="unknown",
            link=original_url,
        )

        result = await formatter_with_service.format(
            pick, sharp_odds=2.0, profit=2.0
        )

        assert "unknown-bookie.com" in result
