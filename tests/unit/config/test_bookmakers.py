"""Unit tests for BookmakerConfig.

Tests cover:
- Default and custom instantiation
- Validation rules
- Query methods (is_sharp, is_target, get_channel, is_valid_contrapartida)
- API source parameter generation
- Bookmaker entity creation
- Factory methods
"""

import pytest

from src.config.bookmakers import BookmakerConfig
from src.domain.entities.bookmaker import Bookmaker, BookmakerType


class TestBookmakerConfigInstantiation:
    """Tests for BookmakerConfig creation and validation."""
    
    def test_default_creation(self):
        """Verify default configuration is valid."""
        config = BookmakerConfig.create_default()
        
        assert config.sharp_hierarchy == ["pinnaclesports"]
        assert config.target_bookmakers == []
        assert config.channel_mapping == {}
    
    def test_custom_configuration(self):
        """Verify custom configuration works correctly."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports", "bet365"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123456},
        )
        
        assert config.sharp_hierarchy == ["pinnaclesports", "bet365"]
        assert config.is_sharp("pinnaclesports")
        assert config.is_sharp("bet365")
        assert config.is_target("retabet_apuestas")
    
    def test_immutability(self):
        """Verify configuration is frozen."""
        config = BookmakerConfig.create_default()
        
        with pytest.raises(Exception):  # FrozenInstanceError
            config.sharp_hierarchy = ["bet365"]
    
    def test_legacy_factory(self):
        """Verify legacy factory creates valid configuration."""
        config = BookmakerConfig.from_legacy()
        
        assert "pinnaclesports" in config.sharp_hierarchy
        assert "retabet_apuestas" in config.target_bookmakers
        assert "yaasscasino" in config.target_bookmakers


class TestBookmakerConfigValidation:
    """Tests for validation rules."""
    
    def test_empty_sharp_hierarchy_raises(self):
        """Verify empty sharp hierarchy raises error."""
        with pytest.raises(ValueError) as exc_info:
            BookmakerConfig(
                sharp_hierarchy=[],
                target_bookmakers=[],
                channel_mapping={},
            )
        
        assert "at least one bookmaker" in str(exc_info.value)
    
    def test_missing_channel_mapping_raises(self):
        """Verify missing channel mapping raises error."""
        with pytest.raises(ValueError) as exc_info:
            BookmakerConfig(
                sharp_hierarchy=["pinnaclesports"],
                target_bookmakers=["retabet_apuestas"],
                channel_mapping={},  # Missing retabet_apuestas channel
            )
        
        assert "Missing channel mapping" in str(exc_info.value)
        assert "retabet_apuestas" in str(exc_info.value)
    
    def test_overlap_sharp_target_raises(self):
        """Verify overlap between sharps and targets raises error."""
        with pytest.raises(ValueError) as exc_info:
            BookmakerConfig(
                sharp_hierarchy=["pinnaclesports"],
                target_bookmakers=["pinnaclesports"],  # Also in sharp!
                channel_mapping={"pinnaclesports": -123},
            )
        
        assert "cannot be both sharp and target" in str(exc_info.value)
    
    def test_valid_configuration_passes(self):
        """Verify valid configuration passes all checks."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas", "yaasscasino"],
            channel_mapping={
                "retabet_apuestas": -123,
                "yaasscasino": -456,
            },
        )
        
        assert config.is_sharp("pinnaclesports")
        assert config.is_target("retabet_apuestas")


class TestIsSharp:
    """Tests for is_sharp method."""
    
    def test_is_sharp_true_for_sharp(self):
        """Verify is_sharp returns True for sharp bookmakers."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports", "bet365"],
            target_bookmakers=[],
            channel_mapping={},
        )
        
        assert config.is_sharp("pinnaclesports") is True
        assert config.is_sharp("bet365") is True
    
    def test_is_sharp_false_for_target(self):
        """Verify is_sharp returns False for targets."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123},
        )
        
        assert config.is_sharp("retabet_apuestas") is False
    
    def test_is_sharp_false_for_unknown(self):
        """Verify is_sharp returns False for unknown bookmakers."""
        config = BookmakerConfig.create_default()
        
        assert config.is_sharp("unknown_bookie") is False


class TestIsTarget:
    """Tests for is_target method."""
    
    def test_is_target_true_for_target(self):
        """Verify is_target returns True for targets."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas", "yaasscasino"],
            channel_mapping={
                "retabet_apuestas": -123,
                "yaasscasino": -456,
            },
        )
        
        assert config.is_target("retabet_apuestas") is True
        assert config.is_target("yaasscasino") is True
    
    def test_is_target_false_for_sharp(self):
        """Verify is_target returns False for sharps."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123},
        )
        
        assert config.is_target("pinnaclesports") is False
    
    def test_is_target_false_for_unknown(self):
        """Verify is_target returns False for unknown."""
        config = BookmakerConfig.create_default()
        
        assert config.is_target("unknown_bookie") is False


class TestGetChannel:
    """Tests for get_channel method."""
    
    def test_get_channel_returns_id(self):
        """Verify get_channel returns correct ID."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -1002294438792},
        )
        
        assert config.get_channel("retabet_apuestas") == -1002294438792
    
    def test_get_channel_returns_none_for_unknown(self):
        """Verify get_channel returns None for unknown."""
        config = BookmakerConfig.create_default()
        
        assert config.get_channel("unknown_bookie") is None
    
    def test_get_channel_negative_id(self):
        """Verify negative channel IDs work (Telegram format)."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123456789},
        )
        
        assert config.get_channel("retabet_apuestas") == -123456789


class TestIsValidContrapartida:
    """Tests for is_valid_contrapartida method."""
    
    def test_valid_contrapartida_with_restrictions(self):
        """Verify contrapartida validation with restrictions."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports", "bet365"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123},
            allowed_contrapartidas={"retabet_apuestas": ["pinnaclesports"]},
        )
        
        # pinnaclesports is allowed
        assert config.is_valid_contrapartida("retabet_apuestas", "pinnaclesports") is True
        # bet365 is NOT allowed
        assert config.is_valid_contrapartida("retabet_apuestas", "bet365") is False
    
    def test_valid_contrapartida_no_restrictions(self):
        """Verify all sharps valid when no restrictions defined."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports", "bet365"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123},
            allowed_contrapartidas={},  # No restrictions
        )
        
        # All sharps are valid
        assert config.is_valid_contrapartida("retabet_apuestas", "pinnaclesports") is True
        assert config.is_valid_contrapartida("retabet_apuestas", "bet365") is True
    
    def test_invalid_contrapartida_non_sharp(self):
        """Verify non-sharp bookmaker returns False."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123},
        )
        
        # retabet is not a sharp, so invalid as contrapartida
        assert config.is_valid_contrapartida("retabet_apuestas", "retabet_apuestas") is False


class TestGetApiSourceParam:
    """Tests for get_api_source_param method."""
    
    def test_api_source_param_format(self):
        """Verify pipe-separated format."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas", "yaasscasino"],
            channel_mapping={
                "retabet_apuestas": -123,
                "yaasscasino": -456,
            },
        )
        
        source = config.get_api_source_param()
        
        assert "pinnaclesports" in source
        assert "retabet_apuestas" in source
        assert "yaasscasino" in source
        assert "|" in source
    
    def test_api_source_no_duplicates(self):
        """Verify no duplicate bookmakers in source."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123},
        )
        
        source = config.get_api_source_param()
        parts = source.split("|")
        
        assert len(parts) == len(set(parts))  # No duplicates


class TestGetFirstSharp:
    """Tests for get_first_sharp method."""
    
    def test_get_first_sharp_by_priority(self):
        """Verify first sharp returned by hierarchy priority."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports", "bet365"],
            target_bookmakers=[],
            channel_mapping={},
        )
        
        # pinnaclesports has higher priority
        result = config.get_first_sharp(["bet365", "pinnaclesports"])
        assert result == "pinnaclesports"
    
    def test_get_first_sharp_returns_none_if_no_match(self):
        """Verify None returned when no sharp found."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=[],
            channel_mapping={},
        )
        
        result = config.get_first_sharp(["retabet_apuestas", "yaasscasino"])
        assert result is None


class TestToBookmakerEntities:
    """Tests for to_bookmaker_entities method."""
    
    def test_creates_sharp_entities(self):
        """Verify sharp Bookmaker entities are created."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123},
        )
        
        entities = config.to_bookmaker_entities()
        
        assert "pinnaclesports" in entities
        assert entities["pinnaclesports"].is_sharp
        assert entities["pinnaclesports"].bookmaker_type == BookmakerType.SHARP
    
    def test_creates_soft_entities_with_channel(self):
        """Verify soft Bookmaker entities have channel IDs."""
        config = BookmakerConfig(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=["retabet_apuestas"],
            channel_mapping={"retabet_apuestas": -123456},
        )
        
        entities = config.to_bookmaker_entities()
        
        assert "retabet_apuestas" in entities
        assert entities["retabet_apuestas"].is_soft
        assert entities["retabet_apuestas"].channel_id == -123456
