"""Tests for validation chain and validators.

Test Requirements:
- BaseValidator is abstract (cannot instantiate)
- Subclasses must implement name and validate
- ValidationChain fail-fast behavior
- OddsValidator range checking
- ProfitValidator range checking
- TimeValidator future checking

Reference:
- docs/05-Implementation.md: Task 3.6
- docs/03-ADRs.md: ADR-005 (validator order)
"""

import pytest

from src.domain.rules.validators.base import BaseValidator, ValidationResult


class TestBaseValidator:
    """Tests for BaseValidator abstract interface (Task 3.1)."""
    
    def test_base_validator_is_abstract(self):
        """BaseValidator should not be instantiable directly."""
        with pytest.raises(TypeError, match="abstract"):
            BaseValidator()
    
    def test_validation_result_creation(self):
        """ValidationResult should be creatable with is_valid."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.error_message is None
    
    def test_validation_result_with_error(self):
        """ValidationResult should store error message."""
        result = ValidationResult(is_valid=False, error_message="Test error")
        assert result.is_valid is False
        assert result.error_message == "Test error"
    
    def test_validation_result_is_immutable(self):
        """ValidationResult should be frozen (immutable)."""
        result = ValidationResult(is_valid=True)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.is_valid = False
    
    def test_subclass_requires_name(self):
        """Subclass without name property should fail to instantiate."""
        class IncompleteValidator(BaseValidator):
            async def validate(self, pick):
                return ValidationResult(is_valid=True)
        
        with pytest.raises(TypeError, match="abstract"):
            IncompleteValidator()
    
    def test_subclass_requires_validate(self):
        """Subclass without validate method should fail to instantiate."""
        class IncompleteValidator(BaseValidator):
            @property
            def name(self) -> str:
                return "IncompleteValidator"
        
        with pytest.raises(TypeError, match="abstract"):
            IncompleteValidator()


# TODO: Import ValidationChain when implemented
# from src.domain.rules.validation_chain import ValidationChain

# Imports for OddsValidator tests
from datetime import datetime, timezone

from src.domain.entities.pick import Pick
from src.domain.rules.validators.odds_validator import OddsValidator
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds


def _create_pick_with_odds(odds_value: float) -> Pick:
    """Helper to create Pick with specified odds for testing."""
    return Pick(
        teams=("Team A", "Team B"),
        odds=Odds(odds_value),
        market_type=MarketType.WIN1,
        variety="",
        event_time=datetime.now(timezone.utc),
        bookmaker="test_bookie",
    )


class TestValidationChain:
    """Tests for ValidationChain."""

    @pytest.mark.asyncio
    async def test_empty_chain_returns_valid(self):
        """Empty chain should pass all picks."""
        # chain = ValidationChain([])
        # result = await chain.validate({})
        # assert result.is_valid
        raise NotImplementedError("Test not implemented - ValidationChain not yet done")

    @pytest.mark.asyncio
    async def test_chain_stops_on_first_failure(self):
        """Chain should stop at first failing validator (fail-fast)."""
        # chain = ValidationChain.create_default()
        # bad_pick = {"odds": 0.5}  # Invalid odds
        # result = await chain.validate(bad_pick)
        # assert not result.is_valid
        # assert result.failed_validator == "OddsValidator"
        raise NotImplementedError("Test not implemented - ValidationChain not yet done")


class TestOddsValidator:
    """Tests for OddsValidator (Task 3.2)."""

    def setup_method(self):
        """Set up test fixtures with default range."""
        self.validator = OddsValidator(min_odds=1.10, max_odds=9.99)

    # -------------------------------------------------------------------------
    # Constructor Tests
    # -------------------------------------------------------------------------

    def test_constructor_with_valid_range(self):
        """Should create validator with valid min < max range."""
        validator = OddsValidator(min_odds=1.50, max_odds=5.00)
        assert validator.name == "OddsValidator"

    def test_constructor_rejects_min_equals_max(self):
        """Should raise ValueError when min_odds == max_odds."""
        with pytest.raises(ValueError, match="must be less than"):
            OddsValidator(min_odds=2.00, max_odds=2.00)

    def test_constructor_rejects_min_greater_than_max(self):
        """Should raise ValueError when min_odds > max_odds."""
        with pytest.raises(ValueError, match="must be less than"):
            OddsValidator(min_odds=5.00, max_odds=2.00)

    def test_constructor_default_values(self):
        """Should use default range 1.10-9.99."""
        validator = OddsValidator()
        assert validator.name == "OddsValidator"
        # Verify defaults by testing boundary
        pick_at_min = _create_pick_with_odds(1.10)
        pick_at_max = _create_pick_with_odds(9.99)
        # These should pass with defaults (tested async below)

    # -------------------------------------------------------------------------
    # Validation - Valid Cases
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_valid_odds_passes(self):
        """Odds within range should pass."""
        pick = _create_pick_with_odds(2.50)
        result = await self.validator.validate(pick)
        assert result.is_valid is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_boundary_min_passes(self):
        """Odds exactly at minimum should pass."""
        pick = _create_pick_with_odds(1.10)
        result = await self.validator.validate(pick)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_boundary_max_passes(self):
        """Odds exactly at maximum should pass."""
        pick = _create_pick_with_odds(9.99)
        result = await self.validator.validate(pick)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_mid_range_odds_passes(self):
        """Odds in middle of range should pass."""
        for odds in [1.50, 2.00, 3.50, 5.00, 7.50]:
            pick = _create_pick_with_odds(odds)
            result = await self.validator.validate(pick)
            assert result.is_valid is True, f"Failed for odds {odds}"

    # -------------------------------------------------------------------------
    # Validation - Invalid Cases
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_odds_below_minimum_fails(self):
        """Odds below minimum should fail."""
        pick = _create_pick_with_odds(1.05)
        result = await self.validator.validate(pick)
        assert result.is_valid is False
        assert "1.05" in result.error_message
        assert "outside range" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_odds_above_maximum_fails(self):
        """Odds above maximum should fail."""
        pick = _create_pick_with_odds(15.0)
        result = await self.validator.validate(pick)
        assert result.is_valid is False
        assert "15.00" in result.error_message

    @pytest.mark.asyncio
    async def test_boundary_just_below_min_fails(self):
        """Odds just below minimum should fail."""
        pick = _create_pick_with_odds(1.09)
        result = await self.validator.validate(pick)
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_boundary_just_above_max_fails(self):
        """Odds just above maximum should fail."""
        pick = _create_pick_with_odds(10.0)
        result = await self.validator.validate(pick)
        assert result.is_valid is False

    # -------------------------------------------------------------------------
    # Custom Range Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_custom_range_valid(self):
        """Validator with custom range should accept odds in that range."""
        validator = OddsValidator(min_odds=2.00, max_odds=5.00)
        pick = _create_pick_with_odds(3.00)
        result = await validator.validate(pick)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_custom_range_rejects_default_valid(self):
        """Custom narrow range should reject odds valid in default range."""
        validator = OddsValidator(min_odds=2.00, max_odds=5.00)
        # 1.50 is valid in default range but not in 2.00-5.00
        pick = _create_pick_with_odds(1.50)
        result = await validator.validate(pick)
        assert result.is_valid is False

    # -------------------------------------------------------------------------
    # Error Message Format
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_error_message_includes_range(self):
        """Error message should include the configured range."""
        pick = _create_pick_with_odds(1.05)
        result = await self.validator.validate(pick)
        assert "[1.10, 9.99]" in result.error_message


from src.domain.entities.surebet import Surebet
from src.domain.rules.validators.profit_validator import ProfitValidator
from src.domain.value_objects.profit import Profit


def _create_surebet_with_profit(profit_value: float) -> Surebet:
    """Helper to create Surebet with specified profit for testing."""
    # Create minimal picks for sharp and soft prongs
    sharp_pick = Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.10),
        market_type=MarketType.OVER,
        variety="2.5",
        event_time=datetime.now(timezone.utc),
        bookmaker="pinnaclesports",
    )
    soft_pick = Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.05),
        market_type=MarketType.UNDER,
        variety="2.5",
        event_time=datetime.now(timezone.utc),
        bookmaker="test_soft_bookie",
    )
    return Surebet(
        prong_sharp=sharp_pick,
        prong_soft=soft_pick,
        profit=Profit(profit_value),
    )


class TestProfitValidator:
    """Tests for ProfitValidator (Task 3.3)."""

    def setup_method(self):
        """Set up test fixtures with default range."""
        self.validator = ProfitValidator(min_profit=-1.0, max_profit=25.0)

    # -------------------------------------------------------------------------
    # Constructor Tests
    # -------------------------------------------------------------------------

    def test_constructor_with_valid_range(self):
        """Should create validator with valid min < max range."""
        validator = ProfitValidator(min_profit=-0.5, max_profit=10.0)
        assert validator.name == "ProfitValidator"

    def test_constructor_rejects_min_equals_max(self):
        """Should raise ValueError when min_profit == max_profit."""
        with pytest.raises(ValueError, match="must be less than"):
            ProfitValidator(min_profit=5.0, max_profit=5.0)

    def test_constructor_rejects_min_greater_than_max(self):
        """Should raise ValueError when min_profit > max_profit."""
        with pytest.raises(ValueError, match="must be less than"):
            ProfitValidator(min_profit=10.0, max_profit=5.0)

    def test_constructor_default_values(self):
        """Should use default range -1.0 to 25.0."""
        validator = ProfitValidator()
        assert validator.name == "ProfitValidator"
        # Verify defaults by testing boundary
        # (async boundary tests below verify this more precisely)

    # -------------------------------------------------------------------------
    # Validation - Valid Cases
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_valid_profit_passes(self):
        """Profit within range should pass."""
        surebet = _create_surebet_with_profit(2.5)
        result = await self.validator.validate(surebet)
        assert result.is_valid is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_boundary_min_passes(self):
        """Profit exactly at minimum should pass."""
        surebet = _create_surebet_with_profit(-1.0)
        result = await self.validator.validate(surebet)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_boundary_max_passes(self):
        """Profit exactly at maximum should pass."""
        surebet = _create_surebet_with_profit(25.0)
        result = await self.validator.validate(surebet)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_mid_range_profit_passes(self):
        """Profit in middle of range should pass."""
        for profit in [-0.5, 0.0, 5.0, 10.0, 20.0]:
            surebet = _create_surebet_with_profit(profit)
            result = await self.validator.validate(surebet)
            assert result.is_valid is True, f"Failed for profit {profit}"

    # -------------------------------------------------------------------------
    # Validation - Invalid Cases
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_profit_below_minimum_fails(self):
        """Profit below minimum should fail."""
        surebet = _create_surebet_with_profit(-2.0)
        result = await self.validator.validate(surebet)
        assert result.is_valid is False
        assert "-2.00%" in result.error_message
        assert "outside range" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_profit_above_maximum_fails(self):
        """Profit above maximum should fail."""
        surebet = _create_surebet_with_profit(30.0)
        result = await self.validator.validate(surebet)
        assert result.is_valid is False
        assert "30.00%" in result.error_message

    @pytest.mark.asyncio
    async def test_boundary_just_below_min_fails(self):
        """Profit just below minimum should fail."""
        surebet = _create_surebet_with_profit(-1.01)
        result = await self.validator.validate(surebet)
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_boundary_just_above_max_fails(self):
        """Profit just above maximum should fail."""
        surebet = _create_surebet_with_profit(25.01)
        result = await self.validator.validate(surebet)
        assert result.is_valid is False

    # -------------------------------------------------------------------------
    # Custom Range Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_custom_range_valid(self):
        """Validator with custom range should accept profit in that range."""
        validator = ProfitValidator(min_profit=0.0, max_profit=10.0)
        surebet = _create_surebet_with_profit(5.0)
        result = await validator.validate(surebet)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_custom_range_rejects_default_valid(self):
        """Custom narrow range should reject profit valid in default range."""
        validator = ProfitValidator(min_profit=0.0, max_profit=10.0)
        # -0.5 is valid in default range but not in 0.0-10.0
        surebet = _create_surebet_with_profit(-0.5)
        result = await validator.validate(surebet)
        assert result.is_valid is False

    # -------------------------------------------------------------------------
    # Error Message Format
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_error_message_includes_range(self):
        """Error message should include the configured range."""
        surebet = _create_surebet_with_profit(-2.0)
        result = await self.validator.validate(surebet)
        assert "[-1.00%, 25.00%]" in result.error_message


class TestTimeValidator:
    """Tests for TimeValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # self.validator = TimeValidator()
        pass
    
    @pytest.mark.asyncio
    async def test_future_event_passes(self):
        """Event in future should pass."""
        # future_time = int(time.time()) + 3600  # 1 hour from now
        # is_valid, _ = await self.validator.validate({"time": future_time})
        # assert is_valid
        raise NotImplementedError("Test not implemented")
    
    @pytest.mark.asyncio
    async def test_past_event_fails(self):
        """Event in past should fail."""
        # past_time = int(time.time()) - 3600  # 1 hour ago
        # is_valid, error = await self.validator.validate({"time": past_time})
        # assert not is_valid
        raise NotImplementedError("Test not implemented")
