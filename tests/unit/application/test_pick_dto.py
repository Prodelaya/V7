"""Unit tests for PickDTO.

Tests for application/dto/pick_dto.py covering:
- from_api_response() parsing and validation
- to_pick() and to_surebet() conversions
- Convenience properties for PickHandler
- Error handling for invalid configurations
"""

from datetime import datetime, timezone

import pytest

from src.application.dto.pick_dto import PickDTO
from src.config.bookmakers import BookmakerConfig
from src.domain.entities.pick import Pick
from src.domain.entities.surebet import Surebet

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def valid_api_response() -> dict:
    """Valid API response with 2 prongs."""
    future_time = int((datetime.now(timezone.utc).timestamp() + 3600) * 1000)
    return {
        "id": 785141488,
        "profit": 2.5,
        "created": 1684229420000,
        "prongs": [
            {
                "teams": ["Fnatic", "G2"],
                "value": 2.10,
                "bk": "pinnaclesports",
                "time": future_time,
                "type": {"type": "over", "variety": "2.5"},
                "tournament": "BLAST Paris Major",
                "sport_id": "CounterStrike",
            },
            {
                "teams": ["Fnatic", "G2"],
                "value": 2.05,
                "bk": "retabet_apuestas",
                "time": future_time,
                "type": {"type": "under", "variety": "2.5"},
                "tournament": "BLAST Paris Major",
                "sport_id": "CounterStrike",
            },
        ],
    }


@pytest.fixture
def bookmaker_config() -> BookmakerConfig:
    """Valid bookmaker configuration."""
    return BookmakerConfig(
        sharp_hierarchy=["pinnaclesports"],
        target_bookmakers=["retabet_apuestas", "yaasscasino"],
        channel_mapping={
            "retabet_apuestas": -1002294438792,
            "yaasscasino": -1002360901387,
        },
        allowed_contrapartidas={
            "retabet_apuestas": ["pinnaclesports"],
            "yaasscasino": ["pinnaclesports"],
        },
    )


@pytest.fixture
def bookmaker_config_no_restrictions() -> BookmakerConfig:
    """BookmakerConfig without contrapartida restrictions."""
    return BookmakerConfig(
        sharp_hierarchy=["pinnaclesports", "bet365"],
        target_bookmakers=["retabet_apuestas"],
        channel_mapping={
            "retabet_apuestas": -1002294438792,
        },
        # No allowed_contrapartidas = all sharps are allowed
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# from_api_response() Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestFromApiResponse:
    """Tests for PickDTO.from_api_response()."""

    def test_valid_surebet(self, valid_api_response, bookmaker_config):
        """Test happy path with valid API response."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)

        assert dto is not None
        assert dto.channel_id == -1002294438792
        assert dto.soft_bookmaker == "retabet_apuestas"
        assert dto.sharp_bookmaker == "pinnaclesports"

    def test_channel_id_correctly_extracted(self, valid_api_response, bookmaker_config):
        """Test that channel_id is extracted from BookmakerConfig."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        assert dto.channel_id == bookmaker_config.get_channel("retabet_apuestas")

    def test_profit_correctly_extracted(self, valid_api_response, bookmaker_config):
        """Test that profit is correctly extracted."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        assert dto.profit == 2.5

    def test_missing_prongs_raises_error(self, bookmaker_config):
        """Test error when prongs array is missing."""
        data = {"id": 123, "profit": 2.5}

        with pytest.raises(ValueError, match="Expected exactly 2 prongs"):
            PickDTO.from_api_response(data, bookmaker_config)

    def test_single_prong_raises_error(self, valid_api_response, bookmaker_config):
        """Test error when only one prong is present."""
        valid_api_response["prongs"] = [valid_api_response["prongs"][0]]

        with pytest.raises(ValueError, match="Expected exactly 2 prongs"):
            PickDTO.from_api_response(valid_api_response, bookmaker_config)

    def test_no_sharp_bookmaker_raises_error(self, bookmaker_config):
        """Test error when no sharp bookmaker is found in prongs."""
        future_time = int((datetime.now(timezone.utc).timestamp() + 3600) * 1000)
        data = {
            "profit": 2.5,
            "prongs": [
                {
                    "teams": ["A", "B"],
                    "value": 2.10,
                    "bk": "unknown_bk1",
                    "time": future_time,
                    "type": {"type": "over", "variety": "2.5"},
                },
                {
                    "teams": ["A", "B"],
                    "value": 2.05,
                    "bk": "unknown_bk2",
                    "time": future_time,
                    "type": {"type": "under", "variety": "2.5"},
                },
            ],
        }

        with pytest.raises(ValueError, match="No sharp bookmaker found"):
            PickDTO.from_api_response(data, bookmaker_config)

    def test_soft_not_in_targets_raises_error(self, bookmaker_config):
        """Test error when soft bookmaker is not in target_bookmakers."""
        future_time = int((datetime.now(timezone.utc).timestamp() + 3600) * 1000)
        data = {
            "profit": 2.5,
            "prongs": [
                {
                    "teams": ["A", "B"],
                    "value": 2.10,
                    "bk": "pinnaclesports",  # Sharp
                    "time": future_time,
                    "type": {"type": "over", "variety": "2.5"},
                },
                {
                    "teams": ["A", "B"],
                    "value": 2.05,
                    "bk": "unknown_soft",  # Not in targets
                    "time": future_time,
                    "type": {"type": "under", "variety": "2.5"},
                },
            ],
        }

        with pytest.raises(ValueError, match="not a target bookmaker"):
            PickDTO.from_api_response(data, bookmaker_config)

    def test_invalid_contrapartida_raises_error(self):
        """Test error when sharp is not an allowed contrapartida for soft."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports", "bet365"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123456},
            allowed_contrapartidas={
                "retabet_apuestas": ["bet365"],  # Only bet365 allowed, not pinnacle
            },
        )

        future_time = int((datetime.now(timezone.utc).timestamp() + 3600) * 1000)
        data = {
            "profit": 2.5,
            "prongs": [
                {
                    "teams": ["A", "B"],
                    "value": 2.10,
                    "bk": "pinnaclesports",  # Not allowed for retabet
                    "time": future_time,
                    "type": {"type": "over", "variety": "2.5"},
                },
                {
                    "teams": ["A", "B"],
                    "value": 2.05,
                    "bk": "retabet_apuestas",
                    "time": future_time,
                    "type": {"type": "under", "variety": "2.5"},
                },
            ],
        }

        with pytest.raises(ValueError, match="not an allowed contrapartida"):
            PickDTO.from_api_response(data, config)

    def test_no_contrapartida_restrictions_allows_all_sharps(
        self, valid_api_response, bookmaker_config_no_restrictions
    ):
        """Test that all sharps are allowed when no restrictions configured."""
        dto = PickDTO.from_api_response(
            valid_api_response, bookmaker_config_no_restrictions
        )
        assert dto.sharp_bookmaker == "pinnaclesports"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# to_pick() Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestToPick:
    """Tests for PickDTO.to_pick()."""

    def test_returns_pick_entity(self, valid_api_response, bookmaker_config):
        """Test that to_pick() returns a Pick entity."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        pick = dto.to_pick()

        assert isinstance(pick, Pick)

    def test_returns_soft_prong(self, valid_api_response, bookmaker_config):
        """Test that to_pick() returns the soft bookmaker's prong."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        pick = dto.to_pick()

        assert pick.bookmaker == "retabet_apuestas"

    def test_pick_has_correct_odds(self, valid_api_response, bookmaker_config):
        """Test that Pick has correct odds from soft prong."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        pick = dto.to_pick()

        assert pick.odds.value == 2.05  # Soft prong odds

    def test_pick_has_correct_teams(self, valid_api_response, bookmaker_config):
        """Test that Pick has correct teams."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        pick = dto.to_pick()

        assert pick.teams == ("Fnatic", "G2")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# to_surebet() Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestToSurebet:
    """Tests for PickDTO.to_surebet()."""

    def test_returns_surebet_entity(self, valid_api_response, bookmaker_config):
        """Test that to_surebet() returns a Surebet entity."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        surebet = dto.to_surebet()

        assert isinstance(surebet, Surebet)

    def test_surebet_has_both_prongs(self, valid_api_response, bookmaker_config):
        """Test that Surebet has both sharp and soft prongs."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        surebet = dto.to_surebet()

        assert surebet.prong_sharp is not None
        assert surebet.prong_soft is not None
        assert surebet.prong_sharp.bookmaker == "pinnaclesports"
        assert surebet.prong_soft.bookmaker == "retabet_apuestas"

    def test_surebet_has_correct_profit(self, valid_api_response, bookmaker_config):
        """Test that Surebet has correct profit."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        surebet = dto.to_surebet()

        assert surebet.profit.value == 2.5


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Convenience Properties Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestConvenienceProperties:
    """Tests for convenience properties."""

    def test_profit_property(self, valid_api_response, bookmaker_config):
        """Test profit property returns correct value."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        assert dto.profit == 2.5

    def test_soft_bookmaker_property(self, valid_api_response, bookmaker_config):
        """Test soft_bookmaker property."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        assert dto.soft_bookmaker == "retabet_apuestas"

    def test_sharp_bookmaker_property(self, valid_api_response, bookmaker_config):
        """Test sharp_bookmaker property."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        assert dto.sharp_bookmaker == "pinnaclesports"

    def test_redis_key_property(self, valid_api_response, bookmaker_config):
        """Test redis_key property returns valid key."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        redis_key = dto.redis_key

        assert isinstance(redis_key, str)
        assert "Fnatic" in redis_key
        assert "G2" in redis_key
        assert "retabet_apuestas" in redis_key  # Soft bookmaker in key

    def test_get_opposite_keys(self, valid_api_response, bookmaker_config):
        """Test get_opposite_keys returns list of keys."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        opposite_keys = dto.get_opposite_keys()

        assert isinstance(opposite_keys, list)
        # under → over is opposite
        if opposite_keys:
            assert "over" in opposite_keys[0] or len(opposite_keys) == 0

    def test_channel_id_property(self, valid_api_response, bookmaker_config):
        """Test channel_id is correctly set."""
        dto = PickDTO.from_api_response(valid_api_response, bookmaker_config)
        assert dto.channel_id == -1002294438792
