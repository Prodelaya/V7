"""Tests for OppositeMarketService.

Tests cover:
- get_opposites() for various market types
- get_opposite_keys() for Redis key generation
- Edge cases: unknown markets, no opposites, case insensitivity
- Consistency with MarketType enum and Pick entity

Reference:
- Task 6.3 in docs/05-Implementation.md
- SRS Appendix 6.1: Opposite markets table
"""

from datetime import datetime, timezone

import pytest

from src.domain.entities.pick import Pick
from src.domain.services.opposite_market_service import OppositeMarketService
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds


@pytest.fixture
def service() -> OppositeMarketService:
    """Create OppositeMarketService instance."""
    return OppositeMarketService()


class TestGetOpposites:
    """Tests for get_opposites() method."""

    def test_get_opposites_single_win1(self, service: OppositeMarketService) -> None:
        """win1 has single opposite: win2."""
        result = service.get_opposites("win1")
        assert result == ["win2"]

    def test_get_opposites_single_win2(self, service: OppositeMarketService) -> None:
        """win2 has single opposite: win1."""
        result = service.get_opposites("win2")
        assert result == ["win1"]

    def test_get_opposites_single_over(self, service: OppositeMarketService) -> None:
        """over has single opposite: under."""
        result = service.get_opposites("over")
        assert result == ["under"]

    def test_get_opposites_single_under(self, service: OppositeMarketService) -> None:
        """under has single opposite: over."""
        result = service.get_opposites("under")
        assert result == ["over"]

    def test_get_opposites_single_ah1(self, service: OppositeMarketService) -> None:
        """ah1 (asian handicap) has single opposite: ah2."""
        result = service.get_opposites("ah1")
        assert result == ["ah2"]

    def test_get_opposites_single_odd(self, service: OppositeMarketService) -> None:
        """odd has single opposite: even."""
        result = service.get_opposites("odd")
        assert result == ["even"]

    def test_get_opposites_single_yes(self, service: OppositeMarketService) -> None:
        """yes has single opposite: no."""
        result = service.get_opposites("yes")
        assert result == ["no"]

    def test_get_opposites_multiple_1x(self, service: OppositeMarketService) -> None:
        """_1x (double chance) has multiple opposites: _x2, _12."""
        result = service.get_opposites("_1x")
        assert set(result) == {"_x2", "_12"}

    def test_get_opposites_multiple_x2(self, service: OppositeMarketService) -> None:
        """_x2 (double chance) has multiple opposites: _1x, _12."""
        result = service.get_opposites("_x2")
        assert set(result) == {"_1x", "_12"}

    def test_get_opposites_multiple_12(self, service: OppositeMarketService) -> None:
        """_12 (double chance) has multiple opposites: _1x, _x2."""
        result = service.get_opposites("_12")
        assert set(result) == {"_1x", "_x2"}

    def test_get_opposites_symmetric_over_under(
        self, service: OppositeMarketService
    ) -> None:
        """Verify symmetry: over -> under -> over."""
        opposites_of_over = service.get_opposites("over")
        assert opposites_of_over == ["under"]

        opposites_of_under = service.get_opposites("under")
        assert opposites_of_under == ["over"]

    def test_get_opposites_symmetric_win1_win2(
        self, service: OppositeMarketService
    ) -> None:
        """Verify symmetry: win1 -> win2 -> win1."""
        opposites_of_win1 = service.get_opposites("win1")
        assert opposites_of_win1 == ["win2"]

        opposites_of_win2 = service.get_opposites("win2")
        assert opposites_of_win2 == ["win1"]

    def test_get_opposites_case_insensitive_upper(
        self, service: OppositeMarketService
    ) -> None:
        """OVER should work same as over."""
        result = service.get_opposites("OVER")
        assert result == ["under"]

    def test_get_opposites_case_insensitive_mixed(
        self, service: OppositeMarketService
    ) -> None:
        """Over should work same as over."""
        result = service.get_opposites("Over")
        assert result == ["under"]

    def test_get_opposites_case_insensitive_win1(
        self, service: OppositeMarketService
    ) -> None:
        """WIN1 should work same as win1."""
        result = service.get_opposites("WIN1")
        assert result == ["win2"]

    def test_get_opposites_no_opposite_draw(
        self, service: OppositeMarketService
    ) -> None:
        """draw has no opposite - returns empty list."""
        result = service.get_opposites("draw")
        assert result == []

    def test_get_opposites_unknown_market(
        self, service: OppositeMarketService
    ) -> None:
        """Unknown market returns empty list (not error)."""
        result = service.get_opposites("xyz_unknown_market")
        assert result == []

    def test_get_opposites_eover(self, service: OppositeMarketService) -> None:
        """eover (esports over) has opposite: e_under."""
        result = service.get_opposites("eover")
        assert result == ["e_under"]

    def test_get_opposites_winonly1(self, service: OppositeMarketService) -> None:
        """winonly1 has opposite: winonly2."""
        result = service.get_opposites("winonly1")
        assert result == ["winonly2"]

    def test_get_opposites_win1retx(self, service: OppositeMarketService) -> None:
        """win1retx (draw no bet) has opposite: win2retx."""
        result = service.get_opposites("win1retx")
        assert result == ["win2retx"]

    def test_get_opposites_clean_sheet(self, service: OppositeMarketService) -> None:
        """clean_sheet_1 has opposite: clean_sheet_2."""
        result = service.get_opposites("clean_sheet_1")
        assert result == ["clean_sheet_2"]


class TestGetOppositeKeys:
    """Tests for get_opposite_keys() method."""

    def test_get_opposite_keys_single(self, service: OppositeMarketService) -> None:
        """Generate single opposite key for over -> under."""
        base_key = "TeamA:TeamB:1234567890000:2.5"
        result = service.get_opposite_keys(base_key, "over", "pinnacle")

        assert len(result) == 1
        assert result[0] == "TeamA:TeamB:1234567890000:2.5:under:pinnacle"

    def test_get_opposite_keys_multiple(self, service: OppositeMarketService) -> None:
        """Generate multiple opposite keys for _1x -> [_x2, _12]."""
        base_key = "TeamA:TeamB:1234567890000:"
        result = service.get_opposite_keys(base_key, "_1x", "bookie")

        assert len(result) == 2
        expected = {
            "TeamA:TeamB:1234567890000::_x2:bookie",
            "TeamA:TeamB:1234567890000::_12:bookie",
        }
        assert set(result) == expected

    def test_get_opposite_keys_format(self, service: OppositeMarketService) -> None:
        """Verify key format: base_key:opposite_market:bookmaker."""
        base_key = "Team1:Team2:9999999999999:goals"
        result = service.get_opposite_keys(base_key, "win1", "retabet")

        assert len(result) == 1
        key = result[0]

        # Verify structure
        parts = key.split(":")
        assert len(parts) == 6  # Team1:Team2:timestamp:variety:market:bookie
        assert parts[0] == "Team1"
        assert parts[1] == "Team2"
        assert parts[2] == "9999999999999"
        assert parts[3] == "goals"
        assert parts[4] == "win2"  # opposite of win1
        assert parts[5] == "retabet"

    def test_get_opposite_keys_empty_no_opposite(
        self, service: OppositeMarketService
    ) -> None:
        """Market with no opposite returns empty list."""
        base_key = "TeamA:TeamB:1234567890000:"
        result = service.get_opposite_keys(base_key, "draw", "bookie")

        assert result == []

    def test_get_opposite_keys_empty_unknown_market(
        self, service: OppositeMarketService
    ) -> None:
        """Unknown market returns empty list."""
        base_key = "TeamA:TeamB:1234567890000:"
        result = service.get_opposite_keys(base_key, "unknown_xyz", "bookie")

        assert result == []

    def test_get_opposite_keys_with_special_bookmaker(
        self, service: OppositeMarketService
    ) -> None:
        """Bookmaker with underscores works correctly."""
        base_key = "TeamA:TeamB:1234567890000:map"
        result = service.get_opposite_keys(base_key, "ah1", "retabet_apuestas")

        assert len(result) == 1
        assert result[0] == "TeamA:TeamB:1234567890000:map:ah2:retabet_apuestas"


class TestConsistencyWithMarketTypeEnum:
    """Tests verifying consistency with MarketType.get_opposites()."""

    def test_consistency_win1(self, service: OppositeMarketService) -> None:
        """Service result matches MarketType.WIN1.get_opposites()."""
        service_result = service.get_opposites("win1")
        enum_result = [m.value for m in MarketType.WIN1.get_opposites()]

        assert service_result == enum_result

    def test_consistency_over(self, service: OppositeMarketService) -> None:
        """Service result matches MarketType.OVER.get_opposites()."""
        service_result = service.get_opposites("over")
        enum_result = [m.value for m in MarketType.OVER.get_opposites()]

        assert service_result == enum_result

    def test_consistency_1x(self, service: OppositeMarketService) -> None:
        """Service result matches MarketType._1X.get_opposites()."""
        service_result = set(service.get_opposites("_1x"))
        enum_result = {m.value for m in MarketType._1X.get_opposites()}

        assert service_result == enum_result

    def test_consistency_all_markets_with_opposites(
        self, service: OppositeMarketService
    ) -> None:
        """Service results match enum for all markets with opposites."""
        markets_to_test = [
            ("win1", MarketType.WIN1),
            ("win2", MarketType.WIN2),
            ("over", MarketType.OVER),
            ("under", MarketType.UNDER),
            ("ah1", MarketType.AH1),
            ("ah2", MarketType.AH2),
            ("odd", MarketType.ODD),
            ("even", MarketType.EVEN),
            ("yes", MarketType.YES),
            ("no", MarketType.NO),
        ]

        for market_str, market_enum in markets_to_test:
            service_result = set(service.get_opposites(market_str))
            enum_result = {m.value for m in market_enum.get_opposites()}
            assert service_result == enum_result, f"Mismatch for {market_str}"


class TestConsistencyWithPickEntity:
    """Tests verifying consistency with Pick.get_opposite_keys().

    Note: The service interface is more flexible than Pick.get_opposite_keys().
    The service receives base_key that the caller constructs, allowing different
    key formats. These tests verify the service produces correct opposite markets
    and key structure, not exact match with Pick's specific format.
    """

    @pytest.fixture
    def sample_pick(self) -> Pick:
        """Create a sample Pick for testing."""
        return Pick(
            teams=("TeamA", "TeamB"),
            odds=Odds(2.05),
            market_type=MarketType.OVER,
            variety="2.5",
            event_time=datetime(2025, 12, 31, 15, 0, 0, tzinfo=timezone.utc),
            bookmaker="pinnaclesports",
            tournament="Test League",
            sport_id="Football",
        )

    def test_consistency_opposite_markets(
        self, service: OppositeMarketService, sample_pick: Pick
    ) -> None:
        """Service returns same opposite market types as Pick."""
        # Get opposite market from service
        service_opposites = service.get_opposites(sample_pick.market_type.value)

        # Get opposite market from Pick (extract market from keys)
        pick_keys = sample_pick.get_opposite_keys()
        # Pick format: team1:team2:timestamp:market:variety:bookie
        pick_opposites = [key.split(":")[3] for key in pick_keys]

        assert set(service_opposites) == set(pick_opposites)

    def test_consistency_key_components(
        self, service: OppositeMarketService, sample_pick: Pick
    ) -> None:
        """Service keys contain correct market and bookmaker components."""
        # Use service with a simple base_key format
        base_key = "team1:team2:timestamp:variety"
        service_keys = service.get_opposite_keys(
            base_key,
            sample_pick.market_type.value,
            sample_pick.bookmaker
        )

        # Verify each key ends with :opposite_market:bookmaker
        for key in service_keys:
            parts = key.split(":")
            assert parts[-1] == sample_pick.bookmaker
            assert parts[-2] in service.get_opposites(sample_pick.market_type.value)

    def test_consistency_multiple_markets(self, service: OppositeMarketService) -> None:
        """Test consistency of opposite markets for various market types."""
        markets_to_test = [
            (MarketType.WIN1, "win1", ["win2"]),
            (MarketType.UNDER, "under", ["over"]),
            (MarketType.AH1, "ah1", ["ah2"]),
            (MarketType._1X, "_1x", ["_x2", "_12"]),
        ]

        for market_enum, market_str, expected_opposites in markets_to_test:
            # Verify service returns expected opposites
            service_result = set(service.get_opposites(market_str))
            assert service_result == set(expected_opposites), f"Mismatch for {market_str}"

            # Verify service returns same opposites as enum
            enum_result = {m.value for m in market_enum.get_opposites()}
            assert service_result == enum_result, f"Enum mismatch for {market_str}"
