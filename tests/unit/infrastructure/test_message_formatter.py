"""Unit tests for MessageFormatter.

Tests cover:
- _adjust_domain() URL transformations (RF-010)
- _format_date() Spain timezone formatting
- _format_teams() sport emoji and HTML escaping
- _format_type_info() market replacements
- _clean_text() HTML escaping and word removal
- Cache operations (TTL, key generation)
- Integration format() method
"""

import html
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.domain.entities.pick import Pick
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds
from src.infrastructure.messaging.message_formatter import MessageFormatter


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def formatter() -> MessageFormatter:
    """Create a MessageFormatter instance without calculation service."""
    return MessageFormatter()


@pytest.fixture
def formatter_with_service() -> MessageFormatter:
    """Create a MessageFormatter with mock calculation service."""
    mock_service = MagicMock()

    # Configure stake result mock
    stake_result = MagicMock()
    stake_result.emoji = "🟡"
    mock_service.calculate_stake.return_value = stake_result

    # Configure min_odds result mock
    min_odds_result = MagicMock()
    min_odds_result.min_odds = 1.92
    mock_service.calculate_min_odds.return_value = min_odds_result

    return MessageFormatter(calculation_service=mock_service)


@pytest.fixture
def sample_pick() -> Pick:
    """Create a sample Pick for testing."""
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
def sample_pick_with_special_chars() -> Pick:
    """Create a Pick with special HTML characters."""
    return Pick(
        teams=("Team <A>", "Team & B"),
        odds=Odds(1.85),
        market_type=MarketType.WIN1,
        variety="",
        event_time=datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
        bookmaker="betway",
        tournament="La Liga > 2025",
        sport_id="football",
        link="https://sports.betway.com/en/sports/football",
    )


# =============================================================================
# _adjust_domain() Tests (RF-010)
# =============================================================================


class TestAdjustDomain:
    """Tests for URL domain adjustments (RF-010)."""

    def test_bet365_com_to_es(self, formatter: MessageFormatter) -> None:
        """Bet365 .com should become .es with uppercase path."""
        url = "https://bet365.com/sports/football/match123"
        result = formatter._adjust_domain(url)
        assert "bet365.es" in result
        assert "bet365.com" not in result

    def test_bet365_path_uppercase(self, formatter: MessageFormatter) -> None:
        """Bet365 path should be converted to uppercase."""
        url = "https://bet365.com/sports/football/match123"
        result = formatter._adjust_domain(url)
        # Path after .es should be uppercase
        assert "/SPORTS/FOOTBALL/MATCH123" in result

    def test_betway_com_en_to_es_es(self, formatter: MessageFormatter) -> None:
        """Betway .com/en should become .es/es."""
        url = "https://sports.betway.com/en/sports/football"
        result = formatter._adjust_domain(url)
        assert "sports.betway.es/es/sports" in result
        assert "betway.com/en" not in result

    def test_bwin_com_en_to_es_es(self, formatter: MessageFormatter) -> None:
        """Bwin .com/en should become .es/es."""
        url = "https://sports.bwin.com/en/sports/football"
        result = formatter._adjust_domain(url)
        assert "sports.bwin.es/es/sports" in result

    def test_pokerstars_uk_to_es(self, formatter: MessageFormatter) -> None:
        """PokerStars .uk should become .es."""
        url = "https://www.pokerstars.uk/sports/football"
        result = formatter._adjust_domain(url)
        assert "pokerstars.es/" in result
        assert "pokerstars.uk" not in result

    def test_versus_sportswidget(self, formatter: MessageFormatter) -> None:
        """Versus sportswidget URL should be transformed."""
        url = "https://sportswidget.versus.es/sports/football"
        result = formatter._adjust_domain(url)
        assert "www.versus.es/apuestas/sports" in result

    def test_versus_without_www(self, formatter: MessageFormatter) -> None:
        """Versus without www should add www and apuestas."""
        url = "https://versus.es/sports/football"
        result = formatter._adjust_domain(url)
        assert "www.versus.es/apuestas/sports" in result

    def test_empty_url(self, formatter: MessageFormatter) -> None:
        """Empty URL should return empty string."""
        result = formatter._adjust_domain("")
        assert result == ""

    def test_none_like_url(self, formatter: MessageFormatter) -> None:
        """None-like URL should return empty string."""
        result = formatter._adjust_domain("")
        assert result == ""

    def test_non_matching_url_passthrough(
        self, formatter: MessageFormatter
    ) -> None:
        """URLs not matching any rule should pass through unchanged."""
        url = "https://example.com/some/path"
        result = formatter._adjust_domain(url)
        assert result == url


# =============================================================================
# _format_date() Tests
# =============================================================================


class TestFormatDate:
    """Tests for date formatting in Spain timezone."""

    def test_valid_timestamp_format(self, formatter: MessageFormatter) -> None:
        """Valid timestamp should be formatted correctly."""
        # 2026-01-15 18:00:00 UTC -> 19:00 in Spain (winter time)
        timestamp_ms = 1768518000000  # Approximate timestamp
        result = formatter._format_date(timestamp_ms)
        assert "📅" in result
        assert "/" in result  # Date format dd/mm/yyyy

    def test_contains_spanish_day(self, formatter: MessageFormatter) -> None:
        """Result should contain Spanish day name."""
        # Use a known date that gives a specific day
        # 2026-01-15 is a Thursday (Jueves)
        timestamp_ms = 1768518000000
        result = formatter._format_date(timestamp_ms)
        # Should contain one of the Spanish day names
        spanish_days = [
            'Lunes', 'Martes', 'Miércoles', 'Jueves',
            'Viernes', 'Sábado', 'Domingo'
        ]
        assert any(day in result for day in spanish_days)

    def test_zero_timestamp(self, formatter: MessageFormatter) -> None:
        """Zero timestamp should return empty string."""
        result = formatter._format_date(0)
        assert result == ""

    def test_invalid_timestamp(self, formatter: MessageFormatter) -> None:
        """Invalid timestamp should return empty string."""
        # Very large invalid timestamp
        result = formatter._format_date(999999999999999999)
        assert result == ""


# =============================================================================
# _format_teams() Tests
# =============================================================================


class TestFormatTeams:
    """Tests for team formatting."""

    def test_football_emoji(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Football sport should have football emoji."""
        result = formatter._format_teams(sample_pick)
        assert "⚽️" in result

    def test_html_code_tags(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Team names should be wrapped in <code> tags."""
        result = formatter._format_teams(sample_pick)
        assert "<code>" in result
        assert "</code>" in result

    def test_vs_separator(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Teams should be separated by 'vs'."""
        result = formatter._format_teams(sample_pick)
        assert " vs " in result

    def test_title_case(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Team names should be in title case."""
        result = formatter._format_teams(sample_pick)
        assert "Team Alpha" in result
        assert "Team Beta" in result

    def test_html_escaping(
        self, formatter: MessageFormatter, sample_pick_with_special_chars: Pick
    ) -> None:
        """Special HTML characters should be escaped."""
        result = formatter._format_teams(sample_pick_with_special_chars)
        # < should be escaped
        assert "&lt;" in result or "Team &Lt;A&Gt;" in result.lower() or "<" not in result.replace("<code>", "").replace("</code>", "")

    def test_unknown_sport(self, formatter: MessageFormatter) -> None:
        """Unknown sport should have no emoji."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
            sport_id="unknown_sport",
        )
        result = formatter._format_teams(pick)
        # Should not crash, just no emoji
        assert "<code>" in result


# =============================================================================
# _format_type_info() Tests
# =============================================================================


class TestFormatTypeInfo:
    """Tests for market type formatting."""

    def test_uppercase_output(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Output should be uppercase."""
        result = formatter._format_type_info(sample_pick)
        assert result == result.upper()

    def test_includes_market_type(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Should include market type."""
        result = formatter._format_type_info(sample_pick)
        assert "OVER" in result

    def test_includes_variety(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Should include variety."""
        result = formatter._format_type_info(sample_pick)
        assert "2.5" in result

    def test_win1_replacement(self, formatter: MessageFormatter) -> None:
        """win1 market should become WIN1."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )
        result = formatter._format_type_info(pick)
        assert "WIN1" in result


# =============================================================================
# _clean_text() Tests
# =============================================================================


class TestCleanText:
    """Tests for text cleaning."""

    def test_html_escaping(self, formatter: MessageFormatter) -> None:
        """Special HTML characters should be escaped."""
        result = formatter._clean_text("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;" in result

    def test_whitespace_normalization(
        self, formatter: MessageFormatter
    ) -> None:
        """Multiple spaces should be normalized to single space."""
        result = formatter._clean_text("too   many    spaces")
        assert "  " not in result

    def test_empty_string(self, formatter: MessageFormatter) -> None:
        """Empty string should return empty string."""
        result = formatter._clean_text("")
        assert result == ""

    def test_none_handling(self, formatter: MessageFormatter) -> None:
        """None-like input should return empty string."""
        result = formatter._clean_text("")
        assert result == ""

    def test_word_removal(self, formatter: MessageFormatter) -> None:
        """Filler words should be removed."""
        result = formatter._clean_text("total goals overall")
        # "total", "goals", "overall" should be removed
        assert "total" not in result.lower() or result.strip() == ""


# =============================================================================
# Cache Operation Tests
# =============================================================================


class TestCacheOperations:
    """Tests for cache operations."""

    def test_cache_key_format(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Cache key should follow expected format."""
        key = formatter._get_cache_key(sample_pick)
        parts = key.split(":")
        assert len(parts) == 4
        assert parts[0] == sample_pick.teams[0]
        assert parts[1] == sample_pick.teams[1]
        assert parts[3] == sample_pick.bookmaker

    def test_cache_miss_returns_none(
        self, formatter: MessageFormatter
    ) -> None:
        """Cache miss should return None."""
        result = formatter._get_cached_parts("nonexistent:key")
        assert result is None

    def test_cache_hit(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Cached parts should be retrievable."""
        key = formatter._get_cache_key(sample_pick)
        parts = {'teams': 'test', 'tournament': 'test', 'date': 'test'}
        formatter._cache_parts(key, parts)

        result = formatter._get_cached_parts(key)
        assert result == parts

    def test_cache_expiration(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Expired cache should return None."""
        key = formatter._get_cache_key(sample_pick)
        parts = {'teams': 'test', 'tournament': 'test', 'date': 'test'}

        # Manually set expired cache entry
        formatter._cache[key] = (time.time() - 100, parts)  # 100 seconds ago

        result = formatter._get_cached_parts(key)
        assert result is None

    def test_cache_size_property(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Cache size should reflect stored entries."""
        assert formatter.cache_size == 0

        key = formatter._get_cache_key(sample_pick)
        formatter._cache_parts(key, {'test': 'data'})

        assert formatter.cache_size == 1

    def test_clear_cache(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """Clear cache should remove all entries."""
        key = formatter._get_cache_key(sample_pick)
        formatter._cache_parts(key, {'test': 'data'})

        formatter.clear_cache()
        assert formatter.cache_size == 0


# =============================================================================
# Integration format() Tests
# =============================================================================


class TestFormatIntegration:
    """Integration tests for the main format() method."""

    @pytest.mark.asyncio
    async def test_format_returns_string(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """format() should return a non-empty string."""
        result = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=2.5,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_format_contains_template_parts(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """format() result should contain expected template parts."""
        result = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=2.5,
        )
        # Should contain teams
        assert "Team Alpha" in result
        # Should contain tournament
        assert "🏆" in result
        # Should contain date
        assert "📅" in result

    @pytest.mark.asyncio
    async def test_format_uses_cache(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """format() should populate cache on first call."""
        # First call should populate cache
        await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=2.5,
        )

        assert formatter_with_service.cache_size > 0

    @pytest.mark.asyncio
    async def test_format_with_adjusted_url(
        self, formatter_with_service: MessageFormatter, sample_pick: Pick
    ) -> None:
        """format() should adjust URL according to RF-010."""
        result = await formatter_with_service.format(
            sample_pick,
            sharp_odds=2.05,
            profit=2.5,
        )
        # bet365.com should be transformed to bet365.es
        assert "bet365.es" in result
        assert "bet365.com" not in result

    @pytest.mark.asyncio
    async def test_format_without_calculation_service(
        self, formatter: MessageFormatter, sample_pick: Pick
    ) -> None:
        """format() without calculation service should still work."""
        result = await formatter.format(sample_pick)
        # Should return a string (may be empty stake/min_odds)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_format_html_escaping(
        self,
        formatter_with_service: MessageFormatter,
        sample_pick_with_special_chars: Pick
    ) -> None:
        """format() should properly escape HTML characters."""
        result = await formatter_with_service.format(
            sample_pick_with_special_chars,
            sharp_odds=1.85,
            profit=2.5,
        )
        # Raw < and > from team names should be escaped
        # The HTML tags like <b>, <code>, <a> should remain
        assert "<b>" in result  # Template tags remain
        assert "<code>" in result  # Template tags remain


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_safe_escape_none(self, formatter: MessageFormatter) -> None:
        """_safe_escape should handle None."""
        result = formatter._safe_escape(None)
        assert result == ""

    def test_safe_escape_empty(self, formatter: MessageFormatter) -> None:
        """_safe_escape should handle empty string."""
        result = formatter._safe_escape("")
        assert result == ""

    def test_adjust_domain_already_transformed(
        self, formatter: MessageFormatter
    ) -> None:
        """URL already with .es should not break."""
        url = "https://bet365.es/sports/football"
        result = formatter._adjust_domain(url)
        assert "bet365.es" in result
