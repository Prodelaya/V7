"""Tests for domain entities.

Test Requirements:
- Bookmaker creation and validation
- BookmakerType enum values
- Pick creation, validation, and functionality
- Immutability of entities

Reference:
- docs/05-Implementation.md: Task 1.9
"""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.bookmaker import Bookmaker, BookmakerType
from src.domain.entities.pick import Pick
from src.domain.entities.surebet import Surebet
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds
from src.domain.value_objects.profit import Profit


class TestBookmakerType:
    """Tests for BookmakerType enum."""

    # -------------------------------------------------------------------------
    # Enum Values
    # -------------------------------------------------------------------------

    def test_sharp_value(self) -> None:
        """SHARP should have value 'sharp'."""
        assert BookmakerType.SHARP.value == "sharp"

    def test_soft_value(self) -> None:
        """SOFT should have value 'soft'."""
        assert BookmakerType.SOFT.value == "soft"

    def test_enum_has_two_members(self) -> None:
        """BookmakerType should have exactly 2 members."""
        assert len(BookmakerType) == 2

    def test_enum_members_are_sharp_and_soft(self) -> None:
        """BookmakerType should only contain SHARP and SOFT."""
        members = {member.name for member in BookmakerType}
        assert members == {"SHARP", "SOFT"}


class TestBookmaker:
    """Tests for Bookmaker entity."""

    # -------------------------------------------------------------------------
    # Valid Creation
    # -------------------------------------------------------------------------

    def test_create_sharp_bookmaker(self) -> None:
        """Should create a SHARP bookmaker successfully."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.name == "pinnaclesports"
        assert bookmaker.bookmaker_type == BookmakerType.SHARP

    def test_create_soft_bookmaker(self) -> None:
        """Should create a SOFT bookmaker successfully."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.name == "retabet_apuestas"
        assert bookmaker.bookmaker_type == BookmakerType.SOFT

    def test_create_bookmaker_with_channel(self) -> None:
        """Should create bookmaker with channel_id."""
        bookmaker = Bookmaker(
            name="retabet_apuestas",
            bookmaker_type=BookmakerType.SOFT,
            channel_id=-123456789,
        )
        assert bookmaker.channel_id == -123456789

    def test_create_bookmaker_without_channel(self) -> None:
        """Should create bookmaker without channel_id (None by default)."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.channel_id is None

    def test_create_bookmaker_with_explicit_display_name(self) -> None:
        """Should use explicit display_name when provided."""
        bookmaker = Bookmaker(
            name="pinnaclesports",
            bookmaker_type=BookmakerType.SHARP,
            display_name="Pinnacle Sports",
        )
        assert bookmaker.display_name == "Pinnacle Sports"

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def test_empty_name_raises_error(self) -> None:
        """Empty name should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Bookmaker(name="", bookmaker_type=BookmakerType.SHARP)

    def test_whitespace_only_name_raises_error(self) -> None:
        """Whitespace-only name should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Bookmaker(name="   ", bookmaker_type=BookmakerType.SHARP)

    # -------------------------------------------------------------------------
    # is_sharp Property
    # -------------------------------------------------------------------------

    def test_is_sharp_true_for_sharp_bookmaker(self) -> None:
        """is_sharp should return True for SHARP bookmaker."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.is_sharp is True

    def test_is_sharp_false_for_soft_bookmaker(self) -> None:
        """is_sharp should return False for SOFT bookmaker."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.is_sharp is False

    # -------------------------------------------------------------------------
    # is_soft Property
    # -------------------------------------------------------------------------

    def test_is_soft_true_for_soft_bookmaker(self) -> None:
        """is_soft should return True for SOFT bookmaker."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.is_soft is True

    def test_is_soft_false_for_sharp_bookmaker(self) -> None:
        """is_soft should return False for SHARP bookmaker."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.is_soft is False

    # -------------------------------------------------------------------------
    # has_channel Property
    # -------------------------------------------------------------------------

    def test_has_channel_true_when_set(self) -> None:
        """has_channel should return True when channel_id is set."""
        bookmaker = Bookmaker(
            name="retabet_apuestas",
            bookmaker_type=BookmakerType.SOFT,
            channel_id=-123456789,
        )
        assert bookmaker.has_channel is True

    def test_has_channel_false_when_none(self) -> None:
        """has_channel should return False when channel_id is None."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.has_channel is False

    # -------------------------------------------------------------------------
    # display_name Auto-generation
    # -------------------------------------------------------------------------

    def test_display_name_auto_generated_simple(self) -> None:
        """display_name should be auto-generated from simple name."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.display_name == "Pinnaclesports"

    def test_display_name_auto_generated_with_underscores(self) -> None:
        """display_name should convert underscores to spaces and title case."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.display_name == "Retabet Apuestas"

    def test_display_name_auto_generated_with_multiple_underscores(self) -> None:
        """display_name should handle multiple underscores."""
        bookmaker = Bookmaker(name="admiral_at", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.display_name == "Admiral At"

    # -------------------------------------------------------------------------
    # Factory Method: sharp()
    # -------------------------------------------------------------------------

    def test_sharp_factory_creates_sharp_bookmaker(self) -> None:
        """Bookmaker.sharp() should create a SHARP bookmaker."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        assert bookmaker.is_sharp is True
        assert bookmaker.bookmaker_type == BookmakerType.SHARP

    def test_sharp_factory_with_display_name(self) -> None:
        """Bookmaker.sharp() should accept display_name."""
        bookmaker = Bookmaker.sharp("pinnaclesports", display_name="Pinnacle")
        assert bookmaker.display_name == "Pinnacle"

    def test_sharp_factory_no_channel(self) -> None:
        """Bookmaker.sharp() should not set channel_id."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        assert bookmaker.channel_id is None
        assert bookmaker.has_channel is False

    # -------------------------------------------------------------------------
    # Factory Method: soft()
    # -------------------------------------------------------------------------

    def test_soft_factory_creates_soft_bookmaker(self) -> None:
        """Bookmaker.soft() should create a SOFT bookmaker."""
        bookmaker = Bookmaker.soft("retabet_apuestas")
        assert bookmaker.is_soft is True
        assert bookmaker.bookmaker_type == BookmakerType.SOFT

    def test_soft_factory_with_channel(self) -> None:
        """Bookmaker.soft() should accept channel_id."""
        bookmaker = Bookmaker.soft("retabet_apuestas", channel_id=-123456789)
        assert bookmaker.channel_id == -123456789
        assert bookmaker.has_channel is True

    def test_soft_factory_with_display_name(self) -> None:
        """Bookmaker.soft() should accept display_name."""
        bookmaker = Bookmaker.soft("retabet_apuestas", display_name="Retabet")
        assert bookmaker.display_name == "Retabet"

    def test_soft_factory_without_channel(self) -> None:
        """Bookmaker.soft() without channel_id should have None."""
        bookmaker = Bookmaker.soft("yaasscasino")
        assert bookmaker.channel_id is None
        assert bookmaker.has_channel is False

    # -------------------------------------------------------------------------
    # Immutability
    # -------------------------------------------------------------------------

    def test_bookmaker_is_immutable_name(self) -> None:
        """Bookmaker should be immutable (cannot change name)."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        with pytest.raises(FrozenInstanceError):
            bookmaker.name = "bet365"  # type: ignore[misc]

    def test_bookmaker_is_immutable_type(self) -> None:
        """Bookmaker should be immutable (cannot change bookmaker_type)."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        with pytest.raises(FrozenInstanceError):
            bookmaker.bookmaker_type = BookmakerType.SOFT  # type: ignore[misc]

    def test_bookmaker_is_immutable_channel(self) -> None:
        """Bookmaker should be immutable (cannot change channel_id)."""
        bookmaker = Bookmaker.soft("retabet_apuestas", channel_id=-123)
        with pytest.raises(FrozenInstanceError):
            bookmaker.channel_id = -456  # type: ignore[misc]

    # -------------------------------------------------------------------------
    # Equality (dataclass default)
    # -------------------------------------------------------------------------

    def test_bookmakers_with_same_values_are_equal(self) -> None:
        """Two bookmakers with same values should be equal."""
        bm1 = Bookmaker.sharp("pinnaclesports")
        bm2 = Bookmaker.sharp("pinnaclesports")
        assert bm1 == bm2

    def test_bookmakers_with_different_names_are_not_equal(self) -> None:
        """Two bookmakers with different names should not be equal."""
        bm1 = Bookmaker.sharp("pinnaclesports")
        bm2 = Bookmaker.sharp("bet365")
        assert bm1 != bm2

    def test_bookmakers_with_different_types_are_not_equal(self) -> None:
        """Two bookmakers with different types should not be equal."""
        bm1 = Bookmaker(name="test", bookmaker_type=BookmakerType.SHARP)
        bm2 = Bookmaker(name="test", bookmaker_type=BookmakerType.SOFT)
        assert bm1 != bm2

    # -------------------------------------------------------------------------
    # Real-world Examples
    # -------------------------------------------------------------------------

    def test_pinnacle_is_sharp(self) -> None:
        """Pinnacle should be creatable as SHARP."""
        pinnacle = Bookmaker.sharp("pinnaclesports")
        assert pinnacle.name == "pinnaclesports"
        assert pinnacle.is_sharp is True
        assert pinnacle.is_soft is False
        assert pinnacle.has_channel is False

    def test_retabet_is_soft_with_channel(self) -> None:
        """Retabet should be creatable as SOFT with channel."""
        retabet = Bookmaker.soft("retabet_apuestas", channel_id=-1001234567890)
        assert retabet.name == "retabet_apuestas"
        assert retabet.is_soft is True
        assert retabet.is_sharp is False
        assert retabet.has_channel is True
        assert retabet.display_name == "Retabet Apuestas"


# =============================================================================
# PICK ENTITY TESTS
# =============================================================================


@pytest.fixture
def valid_pick_data() -> dict:
    """Fixture providing valid Pick constructor arguments."""
    return {
        "teams": ("Team A", "Team B"),
        "odds": Odds(2.05),
        "market_type": MarketType.OVER,
        "variety": "2.5",
        "event_time": datetime(2025, 12, 25, 15, 0, 0, tzinfo=timezone.utc),
        "bookmaker": "pinnaclesports",
        "tournament": "Premier League",
        "sport_id": "Football",
    }


@pytest.fixture
def valid_api_response() -> dict:
    """Fixture providing valid API response for a prong."""
    return {
        "id": 460444138,
        "teams": ["Fnatic", "G2"],
        "value": 2.05,
        "bk": "pinnaclesports",
        "time": 1735135200000,  # 2024-12-25 14:00:00 UTC
        "type": {
            "type": "over",
            "variety": "2.5",
            "condition": "2.5",
            "period": "regular",
            "base": "overall",
        },
        "tournament": "BLAST Paris Major",
        "sport_id": "CounterStrike",
        "event_nav": {
            "direct": True,
            "links": [
                {
                    "name": "main",
                    "link": {
                        "method": "GET",
                        "url": "https://www.pinnacle.com/match/12345",
                    },
                }
            ],
        },
    }


class TestPickCreation:
    """Tests for direct Pick creation."""

    def test_create_valid_pick(self, valid_pick_data: dict) -> None:
        """Should create Pick with valid data."""
        pick = Pick(**valid_pick_data)
        assert pick.teams == ("Team A", "Team B")
        assert pick.odds.value == 2.05
        assert pick.market_type == MarketType.OVER
        assert pick.variety == "2.5"
        assert pick.bookmaker == "pinnaclesports"
        assert pick.tournament == "Premier League"
        assert pick.sport_id == "Football"

    def test_pick_with_optional_link(self, valid_pick_data: dict) -> None:
        """Should create Pick with optional link."""
        valid_pick_data["link"] = "https://example.com/bet"
        pick = Pick(**valid_pick_data)
        assert pick.link == "https://example.com/bet"

    def test_pick_defaults(self) -> None:
        """Optional fields should have correct defaults."""
        pick = Pick(
            teams=("Team A", "Team B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )
        assert pick.tournament == ""
        assert pick.sport_id == ""
        assert pick.link is None


class TestPickValidation:
    """Tests for Pick validation in __post_init__."""

    def test_teams_must_have_two_elements(self, valid_pick_data: dict) -> None:
        """teams must have exactly 2 elements."""
        valid_pick_data["teams"] = ("Team A",)
        with pytest.raises(ValueError, match="exactly 2 teams"):
            Pick(**valid_pick_data)

    def test_teams_cannot_have_more_than_two(self, valid_pick_data: dict) -> None:
        """teams cannot have more than 2 elements."""
        valid_pick_data["teams"] = ("Team A", "Team B", "Team C")
        with pytest.raises(ValueError, match="exactly 2 teams"):
            Pick(**valid_pick_data)

    def test_first_team_cannot_be_empty(self, valid_pick_data: dict) -> None:
        """First team name cannot be empty."""
        valid_pick_data["teams"] = ("", "Team B")
        with pytest.raises(ValueError, match="First team name cannot be empty"):
            Pick(**valid_pick_data)

    def test_second_team_cannot_be_empty(self, valid_pick_data: dict) -> None:
        """Second team name cannot be empty."""
        valid_pick_data["teams"] = ("Team A", "")
        with pytest.raises(ValueError, match="Second team name cannot be empty"):
            Pick(**valid_pick_data)

    def test_team_whitespace_only_raises_error(self, valid_pick_data: dict) -> None:
        """Team with only whitespace should raise error."""
        valid_pick_data["teams"] = ("   ", "Team B")
        with pytest.raises(ValueError, match="First team name cannot be empty"):
            Pick(**valid_pick_data)

    def test_bookmaker_cannot_be_empty(self, valid_pick_data: dict) -> None:
        """Bookmaker cannot be empty."""
        valid_pick_data["bookmaker"] = ""
        with pytest.raises(ValueError, match="Bookmaker cannot be empty"):
            Pick(**valid_pick_data)

    def test_bookmaker_whitespace_only_raises_error(self, valid_pick_data: dict) -> None:
        """Bookmaker with only whitespace should raise error."""
        valid_pick_data["bookmaker"] = "   "
        with pytest.raises(ValueError, match="Bookmaker cannot be empty"):
            Pick(**valid_pick_data)

    def test_event_time_must_be_timezone_aware(self, valid_pick_data: dict) -> None:
        """event_time must have timezone info."""
        valid_pick_data["event_time"] = datetime(2025, 12, 25, 15, 0, 0)  # naive
        with pytest.raises(ValueError, match="timezone-aware"):
            Pick(**valid_pick_data)


class TestPickFromApiResponse:
    """Tests for Pick.from_api_response() factory method."""

    def test_create_from_valid_response(self, valid_api_response: dict) -> None:
        """Should create Pick from valid API response."""
        pick = Pick.from_api_response(valid_api_response)
        assert pick.teams == ("Fnatic", "G2")
        assert pick.odds.value == 2.05
        assert pick.market_type == MarketType.OVER
        assert pick.variety == "2.5"
        assert pick.bookmaker == "pinnaclesports"
        assert pick.tournament == "BLAST Paris Major"
        assert pick.sport_id == "CounterStrike"

    def test_timestamp_conversion(self, valid_api_response: dict) -> None:
        """Timestamp in ms should be converted to datetime."""
        pick = Pick.from_api_response(valid_api_response)
        # 1735135200000 ms = 2024-12-25 14:00:00 UTC
        assert pick.event_time.tzinfo == timezone.utc
        assert pick.event_time.year == 2024
        assert pick.event_time.month == 12
        assert pick.event_time.day == 25

    def test_link_extraction(self, valid_api_response: dict) -> None:
        """Should extract link from event_nav."""
        pick = Pick.from_api_response(valid_api_response)
        assert pick.link == "https://www.pinnacle.com/match/12345"

    def test_link_priority_stake_nav(self, valid_api_response: dict) -> None:
        """stake_nav should have priority over event_nav."""
        valid_api_response["stake_nav"] = {
            "links": [{"link": {"url": "https://stake.url"}}]
        }
        pick = Pick.from_api_response(valid_api_response)
        assert pick.link == "https://stake.url"

    def test_link_priority_view_nav(self, valid_api_response: dict) -> None:
        """view_nav should have priority over event_nav."""
        valid_api_response["view_nav"] = {
            "links": [{"link": {"url": "https://view.url"}}]
        }
        pick = Pick.from_api_response(valid_api_response)
        assert pick.link == "https://view.url"

    def test_missing_teams_raises_error(self, valid_api_response: dict) -> None:
        """Should raise error if teams missing."""
        del valid_api_response["teams"]
        with pytest.raises(ValueError, match="Expected 2 teams"):
            Pick.from_api_response(valid_api_response)

    def test_invalid_teams_count_raises_error(self, valid_api_response: dict) -> None:
        """Should raise error if teams has wrong count."""
        valid_api_response["teams"] = ["Only One"]
        with pytest.raises(ValueError, match="Expected 2 teams"):
            Pick.from_api_response(valid_api_response)

    def test_missing_value_raises_error(self, valid_api_response: dict) -> None:
        """Should raise error if odds value missing."""
        del valid_api_response["value"]
        with pytest.raises(ValueError, match="Missing 'value'"):
            Pick.from_api_response(valid_api_response)

    def test_missing_market_type_raises_error(self, valid_api_response: dict) -> None:
        """Should raise error if market type missing."""
        valid_api_response["type"]["type"] = ""
        with pytest.raises(ValueError, match="Missing 'type.type'"):
            Pick.from_api_response(valid_api_response)

    def test_missing_time_raises_error(self, valid_api_response: dict) -> None:
        """Should raise error if time missing."""
        del valid_api_response["time"]
        with pytest.raises(ValueError, match="Missing 'time'"):
            Pick.from_api_response(valid_api_response)

    def test_missing_bookmaker_raises_error(self, valid_api_response: dict) -> None:
        """Should raise error if bookmaker missing."""
        valid_api_response["bk"] = ""
        with pytest.raises(ValueError, match="Missing 'bk'"):
            Pick.from_api_response(valid_api_response)

    def test_unknown_market_becomes_unknown(self, valid_api_response: dict) -> None:
        """Unknown market type should become MarketType.UNKNOWN."""
        valid_api_response["type"]["type"] = "some_unknown_market"
        pick = Pick.from_api_response(valid_api_response)
        assert pick.market_type == MarketType.UNKNOWN

    def test_empty_variety_allowed(self, valid_api_response: dict) -> None:
        """Empty variety should be allowed."""
        valid_api_response["type"]["variety"] = ""
        pick = Pick.from_api_response(valid_api_response)
        assert pick.variety == ""

    def test_no_link_when_nav_missing(self, valid_api_response: dict) -> None:
        """link should be None when no nav elements."""
        del valid_api_response["event_nav"]
        pick = Pick.from_api_response(valid_api_response)
        assert pick.link is None


class TestPickRedisKey:
    """Tests for redis_key property."""

    def test_redis_key_format(self, valid_pick_data: dict) -> None:
        """redis_key should have correct format."""
        pick = Pick(**valid_pick_data)
        key = pick.redis_key
        parts = key.split(":")
        assert len(parts) == 6
        assert parts[0] == "Team A"
        assert parts[1] == "Team B"
        assert parts[3] == "over"
        assert parts[4] == "2.5"
        assert parts[5] == "pinnaclesports"

    def test_redis_key_includes_timestamp(self, valid_pick_data: dict) -> None:
        """redis_key should include timestamp in ms."""
        pick = Pick(**valid_pick_data)
        key = pick.redis_key
        parts = key.split(":")
        timestamp = int(parts[2])
        # 2025-12-25 15:00:00 UTC in ms
        expected_ms = int(valid_pick_data["event_time"].timestamp() * 1000)
        assert timestamp == expected_ms

    def test_different_picks_different_keys(self) -> None:
        """Different picks should have different keys."""
        pick1 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.OVER,
            variety="2.5",
            event_time=datetime.now(timezone.utc),
            bookmaker="bookie1",
        )
        pick2 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.UNDER,  # Different market
            variety="2.5",
            event_time=pick1.event_time,
            bookmaker="bookie1",
        )
        assert pick1.redis_key != pick2.redis_key

    def test_same_pick_same_key(self) -> None:
        """Same pick attributes should produce same key."""
        event_time = datetime.now(timezone.utc)
        pick1 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=event_time,
            bookmaker="test",
        )
        pick2 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=event_time,
            bookmaker="test",
        )
        assert pick1.redis_key == pick2.redis_key


class TestPickOppositeKeys:
    """Tests for get_opposite_keys() method."""

    def test_opposite_keys_for_over(self) -> None:
        """OVER should generate key for UNDER."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.OVER,
            variety="2.5",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )
        opposite_keys = pick.get_opposite_keys()
        assert len(opposite_keys) == 1
        assert "under" in opposite_keys[0]
        assert "over" not in opposite_keys[0]

    def test_opposite_keys_for_win1(self) -> None:
        """WIN1 should generate key for WIN2."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )
        opposite_keys = pick.get_opposite_keys()
        assert len(opposite_keys) == 1
        assert "win2" in opposite_keys[0]

    def test_opposite_keys_for_1x(self) -> None:
        """_1X should generate keys for _X2 and _12."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType._1X,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )
        opposite_keys = pick.get_opposite_keys()
        assert len(opposite_keys) == 2
        key_values = [k.split(":")[3] for k in opposite_keys]
        assert "_x2" in key_values
        assert "_12" in key_values

    def test_no_opposites_for_draw(self) -> None:
        """DRAW has no opposites, should return empty list."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.DRAW,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )
        assert pick.get_opposite_keys() == []

    def test_no_opposites_for_unknown(self) -> None:
        """UNKNOWN market has no opposites."""
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.UNKNOWN,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="test",
        )
        assert pick.get_opposite_keys() == []

    def test_opposite_key_format(self) -> None:
        """Opposite key should preserve base and change only market type."""
        event_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        pick = Pick(
            teams=("Team1", "Team2"),
            odds=Odds(2.0),
            market_type=MarketType.OVER,
            variety="goals",
            event_time=event_time,
            bookmaker="mybookie",
        )
        opposite_keys = pick.get_opposite_keys()
        assert len(opposite_keys) == 1

        # Parse the key
        parts = opposite_keys[0].split(":")
        assert parts[0] == "Team1"
        assert parts[1] == "Team2"
        assert parts[3] == "under"  # Changed from "over"
        assert parts[4] == "goals"  # Same variety
        assert parts[5] == "mybookie"  # Same bookie


class TestPickImmutability:
    """Tests for Pick immutability (frozen dataclass)."""

    def test_cannot_modify_teams(self, valid_pick_data: dict) -> None:
        """Should not be able to modify teams."""
        pick = Pick(**valid_pick_data)
        with pytest.raises(FrozenInstanceError):
            pick.teams = ("X", "Y")  # type: ignore[misc]

    def test_cannot_modify_odds(self, valid_pick_data: dict) -> None:
        """Should not be able to modify odds."""
        pick = Pick(**valid_pick_data)
        with pytest.raises(FrozenInstanceError):
            pick.odds = Odds(3.0)  # type: ignore[misc]

    def test_cannot_modify_bookmaker(self, valid_pick_data: dict) -> None:
        """Should not be able to modify bookmaker."""
        pick = Pick(**valid_pick_data)
        with pytest.raises(FrozenInstanceError):
            pick.bookmaker = "other"  # type: ignore[misc]

    def test_teams_is_tuple(self, valid_pick_data: dict) -> None:
        """teams should be a tuple (immutable)."""
        pick = Pick(**valid_pick_data)
        assert isinstance(pick.teams, tuple)


class TestPickProperties:
    """Tests for additional Pick properties."""

    def test_event_timestamp_ms(self, valid_pick_data: dict) -> None:
        """event_timestamp_ms should return ms timestamp."""
        pick = Pick(**valid_pick_data)
        expected = int(valid_pick_data["event_time"].timestamp() * 1000)
        assert pick.event_timestamp_ms == expected

    def test_is_future_event_true(self) -> None:
        """is_future_event should be True for future events."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=24)
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=future_time,
            bookmaker="test",
        )
        assert pick.is_future_event is True

    def test_is_future_event_false(self) -> None:
        """is_future_event should be False for past events."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=24)
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=past_time,
            bookmaker="test",
        )
        assert pick.is_future_event is False

    def test_seconds_until_event_future(self) -> None:
        """seconds_until_event should be positive for future events."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=future_time,
            bookmaker="test",
        )
        # Should be around 3600 seconds (1 hour)
        assert 3500 < pick.seconds_until_event() < 3700

    def test_seconds_until_event_past(self) -> None:
        """seconds_until_event should be negative for past events."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pick = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=past_time,
            bookmaker="test",
        )
        # Should be around -3600 seconds
        assert -3700 < pick.seconds_until_event() < -3500


class TestPickStringRepresentations:
    """Tests for __str__ and __repr__."""

    def test_str_representation(self, valid_pick_data: dict) -> None:
        """__str__ should provide readable format."""
        pick = Pick(**valid_pick_data)
        result = str(pick)
        assert "Team A" in result
        assert "Team B" in result
        assert "over" in result
        assert "pinnaclesports" in result

    def test_repr_representation(self, valid_pick_data: dict) -> None:
        """__repr__ should include all fields."""
        pick = Pick(**valid_pick_data)
        result = repr(pick)
        assert "Pick(" in result
        assert "teams=" in result
        assert "odds=" in result
        assert "market_type=" in result


class TestPickEquality:
    """Tests for Pick equality (dataclass default)."""

    def test_same_picks_are_equal(self) -> None:
        """Two picks with same values should be equal."""
        event_time = datetime.now(timezone.utc)
        pick1 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=event_time,
            bookmaker="test",
        )
        pick2 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=event_time,
            bookmaker="test",
        )
        assert pick1 == pick2

    def test_different_odds_not_equal(self) -> None:
        """Picks with different odds should not be equal."""
        event_time = datetime.now(timezone.utc)
        pick1 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=event_time,
            bookmaker="test",
        )
        pick2 = Pick(
            teams=("A", "B"),
            odds=Odds(2.5),  # Different
            market_type=MarketType.WIN1,
            variety="",
            event_time=event_time,
            bookmaker="test",
        )
        assert pick1 != pick2


# =============================================================================
# SUREBET ENTITY TESTS
# =============================================================================




@pytest.fixture
def sharp_pick() -> Pick:
    """Fixture providing a valid sharp (Pinnacle) pick."""
    return Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.10),
        market_type=MarketType.OVER,
        variety="2.5",
        event_time=datetime(2025, 12, 25, 15, 0, 0, tzinfo=timezone.utc),
        bookmaker="pinnaclesports",
        tournament="Premier League",
        sport_id="Football",
    )


@pytest.fixture
def soft_pick() -> Pick:
    """Fixture providing a valid soft (Retabet) pick."""
    return Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.05),
        market_type=MarketType.UNDER,
        variety="2.5",
        event_time=datetime(2025, 12, 25, 15, 0, 0, tzinfo=timezone.utc),
        bookmaker="retabet_apuestas",
        tournament="Premier League",
        sport_id="Football",
    )


@pytest.fixture
def valid_surebet_api_response() -> dict:
    """Fixture providing valid API response for a surebet."""
    return {
        "id": 785141488,
        "sort_by": 4609118910833099900,
        "time": 1735135200000,
        "created": 1735000000000,
        "profit": 2.5,
        "roi": 222.6584,
        "prongs": [
            {
                "id": 460444138,
                "teams": ["Fnatic", "G2"],
                "value": 2.10,
                "bk": "pinnaclesports",
                "time": 1735135200000,
                "type": {
                    "type": "over",
                    "variety": "2.5",
                    "condition": "2.5",
                    "period": "regular",
                    "base": "overall",
                },
                "tournament": "BLAST Paris Major",
                "sport_id": "CounterStrike",
            },
            {
                "id": 460444139,
                "teams": ["Fnatic", "G2"],
                "value": 2.05,
                "bk": "retabet_apuestas",
                "time": 1735135200000,
                "type": {
                    "type": "under",
                    "variety": "2.5",
                    "condition": "2.5",
                    "period": "regular",
                    "base": "overall",
                },
                "tournament": "BLAST Paris Major",
                "sport_id": "CounterStrike",
            },
        ],
    }





class TestSurebetCreation:
    """Tests for direct Surebet creation."""

    def test_create_valid_surebet(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """Should create Surebet with valid prongs."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
        )
        assert surebet.prong_sharp == sharp_pick
        assert surebet.prong_soft == soft_pick
        assert surebet.profit.value == 2.5

    def test_create_surebet_with_optional_fields(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """Should create Surebet with optional surebet_id and created."""
        created_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
            surebet_id=12345,
            created=created_time,
        )
        assert surebet.surebet_id == 12345
        assert surebet.created == created_time

    def test_surebet_defaults(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """Optional fields should have correct defaults."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(1.0),
        )
        assert surebet.surebet_id is None
        assert surebet.created is None


class TestSurebetValidation:
    """Tests for Surebet validation in __post_init__."""

    def test_same_bookmaker_raises_error(self, soft_pick: Pick) -> None:
        """prong_sharp and prong_soft cannot be from same bookmaker."""
        # Create two picks from the same bookmaker
        pick1 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="retabet_apuestas",
        )
        pick2 = Pick(
            teams=("A", "B"),
            odds=Odds(2.5),
            market_type=MarketType.WIN2,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="retabet_apuestas",  # Same bookmaker
        )
        with pytest.raises(ValueError, match="cannot be from the same bookmaker"):
            Surebet(
                prong_sharp=pick1,
                prong_soft=pick2,
                profit=Profit(1.0),
            )

    def test_different_bookmakers_allowed(self) -> None:
        """Prongs from different non-sharp bookmakers should be allowed."""
        # Note: Since __post_init__ doesn't validate against SHARP_BOOKMAKERS,
        # this allows for flexible use cases and custom sharp configurations
        pick1 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="bet365",  # Not in default SHARP_BOOKMAKERS
        )
        pick2 = Pick(
            teams=("A", "B"),
            odds=Odds(2.5),
            market_type=MarketType.WIN2,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="retabet_apuestas",
        )
        # This should not raise - validation of sharp/soft is done by from_api_response
        surebet = Surebet(
            prong_sharp=pick1,
            prong_soft=pick2,
            profit=Profit(1.0),
        )
        assert surebet.prong_sharp.bookmaker == "bet365"

    def test_created_must_be_timezone_aware(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """created must have timezone info if provided."""
        naive_time = datetime(2025, 1, 1, 12, 0, 0)  # No timezone
        with pytest.raises(ValueError, match="timezone-aware"):
            Surebet(
                prong_sharp=sharp_pick,
                prong_soft=soft_pick,
                profit=Profit(1.0),
                created=naive_time,
            )


class TestSurebetFromApiResponse:
    """Tests for Surebet.from_api_response() factory method."""

    @pytest.fixture
    def sharps(self) -> frozenset[str]:
        return frozenset({"pinnaclesports"})

    def test_create_from_valid_response(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should create Surebet from valid API response."""
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=sharps
        )
        assert surebet.sharp_bookmaker == "pinnaclesports"
        assert surebet.soft_bookmaker == "retabet_apuestas"
        assert surebet.profit.value == 2.5
        assert surebet.teams == ("Fnatic", "G2")

    def test_determines_roles_correctly_pinnacle_first(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should correctly identify sharp when Pinnacle is first prong."""
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=sharps
        )
        assert surebet.prong_sharp.bookmaker == "pinnaclesports"
        assert surebet.prong_soft.bookmaker == "retabet_apuestas"

    def test_determines_roles_correctly_pinnacle_second(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should correctly identify sharp when Pinnacle is second prong."""
        # Swap the order of prongs
        valid_surebet_api_response["prongs"] = [
            valid_surebet_api_response["prongs"][1],  # retabet first
            valid_surebet_api_response["prongs"][0],  # pinnacle second
        ]
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=sharps
        )
        assert surebet.prong_sharp.bookmaker == "pinnaclesports"
        assert surebet.prong_soft.bookmaker == "retabet_apuestas"

    def test_extracts_surebet_id(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should extract surebet_id from API response."""
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=sharps
        )
        assert surebet.surebet_id == 785141488

    def test_extracts_created_timestamp(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should convert created timestamp from ms to datetime."""
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=sharps
        )
        assert surebet.created is not None
        assert surebet.created.tzinfo == timezone.utc

    def test_missing_profit_raises_error(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should raise error if profit is missing."""
        del valid_surebet_api_response["profit"]
        with pytest.raises(ValueError, match="Missing 'profit'"):
            Surebet.from_api_response(
                valid_surebet_api_response, sharp_bookmakers=sharps
            )

    def test_missing_prongs_raises_error(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should raise error if prongs is missing."""
        del valid_surebet_api_response["prongs"]
        with pytest.raises(ValueError, match="Expected exactly 2 prongs"):
            Surebet.from_api_response(
                valid_surebet_api_response, sharp_bookmakers=sharps
            )

    def test_wrong_prongs_count_raises_error(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should raise error if prongs count is not 2."""
        valid_surebet_api_response["prongs"] = [
            valid_surebet_api_response["prongs"][0]
        ]
        with pytest.raises(ValueError, match="Expected exactly 2 prongs"):
            Surebet.from_api_response(
                valid_surebet_api_response, sharp_bookmakers=sharps
            )

    def test_no_sharp_bookmaker_raises_error(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should raise error if neither prong is from a sharp bookmaker."""
        valid_surebet_api_response["prongs"][0]["bk"] = "bet365"
        valid_surebet_api_response["prongs"][1]["bk"] = "retabet_apuestas"
        with pytest.raises(ValueError, match="No sharp bookmaker found"):
            Surebet.from_api_response(
                valid_surebet_api_response, sharp_bookmakers=sharps
            )

    def test_custom_sharp_bookmakers(
        self, valid_surebet_api_response: dict
    ) -> None:
        """Should accept custom sharp_bookmakers set."""
        # Change first prong to bet365
        valid_surebet_api_response["prongs"][0]["bk"] = "bet365"
        # Use custom sharp set that includes bet365
        custom_sharps = frozenset({"bet365"})
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=custom_sharps
        )
        assert surebet.sharp_bookmaker == "bet365"

    def test_handles_missing_created(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should handle missing created field gracefully."""
        del valid_surebet_api_response["created"]
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=sharps
        )
        assert surebet.created is None

    def test_handles_missing_id(
        self, valid_surebet_api_response: dict, sharps: frozenset[str]
    ) -> None:
        """Should handle missing id field gracefully."""
        del valid_surebet_api_response["id"]
        surebet = Surebet.from_api_response(
            valid_surebet_api_response, sharp_bookmakers=sharps
        )
        assert surebet.surebet_id is None


class TestSurebetToPick:
    """Tests for to_pick() method."""

    def test_to_pick_returns_soft_prong(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """to_pick() should return the soft prong."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        pick = surebet.to_pick()
        assert pick == soft_pick
        assert pick.bookmaker == "retabet_apuestas"

    def test_to_pick_returns_pick_type(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """to_pick() should return Pick instance."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        pick = surebet.to_pick()
        assert isinstance(pick, Pick)


class TestSurebetProperties:
    """Tests for Surebet convenience properties."""

    def test_sharp_odds(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """sharp_odds should return prong_sharp odds."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.sharp_odds.value == 2.10

    def test_soft_odds(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """soft_odds should return prong_soft odds."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.soft_odds.value == 2.05

    def test_sharp_bookmaker(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """sharp_bookmaker should return prong_sharp bookmaker."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.sharp_bookmaker == "pinnaclesports"

    def test_soft_bookmaker(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """soft_bookmaker should return prong_soft bookmaker."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.soft_bookmaker == "retabet_apuestas"

    def test_teams_from_soft_prong(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """teams should return prong_soft teams."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.teams == ("Team A", "Team B")

    def test_event_time_from_soft_prong(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """event_time should return prong_soft event_time."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.event_time == soft_pick.event_time

    def test_tournament_from_soft_prong(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """tournament should return prong_soft tournament."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.tournament == "Premier League"

    def test_sport_id_from_soft_prong(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """sport_id should return prong_soft sport_id."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.sport_id == "Football"

    def test_is_profitable_true(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """is_profitable should be True when profit > 0."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
        )
        assert surebet.is_profitable is True

    def test_is_profitable_false_zero(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """is_profitable should be False when profit == 0."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(0.0),
        )
        assert surebet.is_profitable is False

    def test_is_profitable_false_negative(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """is_profitable should be False when profit < 0."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(-0.5),
        )
        assert surebet.is_profitable is False

    def test_is_acceptable_delegates_to_profit(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """is_acceptable should delegate to Profit.is_acceptable()."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),  # Within acceptable range
        )
        assert surebet.is_acceptable is True

    def test_redis_key_from_soft_prong(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """redis_key should delegate to prong_soft."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.redis_key == soft_pick.redis_key

    def test_get_opposite_keys_from_soft_prong(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """get_opposite_keys should delegate to prong_soft."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        assert surebet.get_opposite_keys() == soft_pick.get_opposite_keys()


class TestSurebetImmutability:
    """Tests for Surebet immutability (frozen dataclass)."""

    def test_cannot_modify_prong_sharp(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """Should not be able to modify prong_sharp."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        new_pick = Pick(
            teams=("X", "Y"),
            odds=Odds(3.0),
            market_type=MarketType.WIN2,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="pinnaclesports",
        )
        with pytest.raises(FrozenInstanceError):
            surebet.prong_sharp = new_pick  # type: ignore[misc]

    def test_cannot_modify_prong_soft(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """Should not be able to modify prong_soft."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        with pytest.raises(FrozenInstanceError):
            surebet.prong_soft = soft_pick  # type: ignore[misc]

    def test_cannot_modify_profit(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """Should not be able to modify profit."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.0),
        )
        with pytest.raises(FrozenInstanceError):
            surebet.profit = Profit(5.0)  # type: ignore[misc]


class TestSurebetStringRepresentations:
    """Tests for __str__ and __repr__."""

    def test_str_representation(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """__str__ should provide readable format."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
        )
        result = str(surebet)
        assert "Team A" in result
        assert "Team B" in result
        assert "pinnaclesports" in result
        assert "retabet_apuestas" in result
        assert "2.5" in result or "2.50" in result

    def test_repr_representation(self, sharp_pick: Pick, soft_pick: Pick) -> None:
        """__repr__ should include all fields."""
        surebet = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
        )
        result = repr(surebet)
        assert "Surebet(" in result
        assert "prong_sharp=" in result
        assert "prong_soft=" in result
        assert "profit=" in result


class TestSurebetEquality:
    """Tests for Surebet equality (dataclass default)."""

    def test_same_surebets_are_equal(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """Two surebets with same values should be equal."""
        surebet1 = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
        )
        surebet2 = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
        )
        assert surebet1 == surebet2

    def test_different_profit_not_equal(
        self, sharp_pick: Pick, soft_pick: Pick
    ) -> None:
        """Surebets with different profit should not be equal."""
        surebet1 = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(2.5),
        )
        surebet2 = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick,
            profit=Profit(3.0),
        )
        assert surebet1 != surebet2

    def test_different_prongs_not_equal(self, sharp_pick: Pick) -> None:
        """Surebets with different prongs should not be equal."""
        soft_pick1 = Pick(
            teams=("A", "B"),
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="retabet_apuestas",
        )
        soft_pick2 = Pick(
            teams=("C", "D"),  # Different teams
            odds=Odds(2.0),
            market_type=MarketType.WIN1,
            variety="",
            event_time=datetime.now(timezone.utc),
            bookmaker="retabet_apuestas",
        )
        surebet1 = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick1,
            profit=Profit(2.5),
        )
        surebet2 = Surebet(
            prong_sharp=sharp_pick,
            prong_soft=soft_pick2,
            profit=Profit(2.5),
        )
        assert surebet1 != surebet2
