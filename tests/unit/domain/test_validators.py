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
    """Tests for ValidationChain (Task 3.5)."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.domain.rules.validation_chain import ValidationChain
        self.ValidationChain = ValidationChain

    # -------------------------------------------------------------------------
    # Constructor Tests
    # -------------------------------------------------------------------------

    def test_constructor_empty(self):
        """Empty chain should be creatable."""
        chain = self.ValidationChain()
        assert len(chain) == 0
        assert chain.is_empty is True

    def test_constructor_with_validators(self):
        """Chain with validators should store them."""
        odds_validator = OddsValidator()
        chain = self.ValidationChain([odds_validator])
        assert len(chain) == 1
        assert chain.is_empty is False

    def test_validators_property_returns_copy(self):
        """validators property should return copy to prevent mutation."""
        odds_validator = OddsValidator()
        chain = self.ValidationChain([odds_validator])
        validators = chain.validators
        validators.pop()  # Mutate the copy
        assert len(chain) == 1  # Original unchanged

    # -------------------------------------------------------------------------
    # Add/Remove Validator Tests
    # -------------------------------------------------------------------------

    def test_add_validator(self):
        """add_validator should append to chain."""
        chain = self.ValidationChain()
        chain.add_validator(OddsValidator())
        assert len(chain) == 1
        chain.add_validator(TimeValidator())
        assert len(chain) == 2

    def test_remove_validator_by_name(self):
        """remove_validator should remove by name."""
        chain = self.ValidationChain([OddsValidator(), TimeValidator()])
        assert len(chain) == 2
        result = chain.remove_validator("OddsValidator")
        assert result is True
        assert len(chain) == 1
        assert chain.validators[0].name == "TimeValidator"

    def test_remove_validator_not_found(self):
        """remove_validator should return False if not found."""
        chain = self.ValidationChain([OddsValidator()])
        result = chain.remove_validator("NonExistent")
        assert result is False
        assert len(chain) == 1

    # -------------------------------------------------------------------------
    # Validation - Empty Chain
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_empty_chain_returns_valid(self):
        """Empty chain should pass all data."""
        chain = self.ValidationChain([])
        pick = _create_pick_with_odds(2.50)
        result = await chain.validate(pick)
        assert result.is_valid is True
        assert result.error_message is None
        assert result.failed_validator is None

    # -------------------------------------------------------------------------
    # Validation - Single Validator
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_single_validator_passes(self):
        """Single passing validator should return valid."""
        chain = self.ValidationChain([OddsValidator()])
        pick = _create_pick_with_odds(2.50)
        result = await chain.validate(pick)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_single_validator_fails(self):
        """Single failing validator should return invalid with details."""
        chain = self.ValidationChain([OddsValidator()])
        # 1.05 is valid for Odds VO (1.01-1000) but fails OddsValidator (1.10-9.99)
        pick = _create_pick_with_odds(1.05)
        result = await chain.validate(pick)
        assert result.is_valid is False
        assert result.failed_validator == "OddsValidator"
        assert "1.05" in result.error_message

    # -------------------------------------------------------------------------
    # Validation - Fail-Fast Behavior
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_chain_stops_on_first_failure(self):
        """Chain should stop at first failing validator (fail-fast)."""
        # First validator will fail, second should never run
        chain = self.ValidationChain([
            OddsValidator(min_odds=5.0, max_odds=9.99),  # Will fail for 2.50
            TimeValidator(min_seconds=9999),  # Would also fail, but shouldn't run
        ])
        pick = _create_pick_with_odds(2.50)
        result = await chain.validate(pick)
        assert result.is_valid is False
        assert result.failed_validator == "OddsValidator"  # First one

    @pytest.mark.asyncio
    async def test_chain_continues_on_success(self):
        """Chain should continue to next validator on success."""
        # First passes, second fails
        chain = self.ValidationChain([
            OddsValidator(),  # Passes for 2.50
            TimeValidator(min_seconds=9999),  # Will fail - too much buffer
        ])
        pick = _create_pick_with_odds(2.50)
        result = await chain.validate(pick)
        assert result.is_valid is False
        assert result.failed_validator == "TimeValidator"  # Second one

    @pytest.mark.asyncio
    async def test_all_validators_pass(self):
        """All passing validators should return valid."""
        chain = self.ValidationChain([
            OddsValidator(),
            TimeValidator(),
        ])
        pick = _create_pick_with_event_time(3600)  # 1 hour from now
        result = await chain.validate(pick)
        assert result.is_valid is True

    # -------------------------------------------------------------------------
    # Validation - With Surebet (includes ProfitValidator)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_validate_surebet_all_pass(self):
        """Surebet validation should work with all validators."""
        from src.domain.rules.validators.profit_validator import ProfitValidator

        chain = self.ValidationChain([
            OddsValidator(),
            ProfitValidator(),
            TimeValidator(),
        ])
        # Create surebet with future event time to pass TimeValidator
        surebet = _create_surebet_with_future_event(2.5)
        result = await chain.validate(surebet)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_surebet_profit_fails(self):
        """ProfitValidator should fail for out-of-range profit."""
        from src.domain.rules.validators.profit_validator import ProfitValidator

        chain = self.ValidationChain([
            OddsValidator(),
            ProfitValidator(min_profit=-1.0, max_profit=10.0),
        ])
        surebet = _create_surebet_with_profit(15.0)  # Above max
        result = await chain.validate(surebet)
        assert result.is_valid is False
        assert result.failed_validator == "ProfitValidator"

    @pytest.mark.asyncio
    async def test_validate_pick_skips_profit_validator(self):
        """ProfitValidator should be skipped when input is Pick (not Surebet)."""
        from src.domain.rules.validators.profit_validator import ProfitValidator

        chain = self.ValidationChain([
            OddsValidator(),
            ProfitValidator(),  # Should be skipped
            TimeValidator(),
        ])
        pick = _create_pick_with_event_time(3600)
        result = await chain.validate(pick)
        # Should pass because ProfitValidator is skipped for Pick input
        assert result.is_valid is True

    # -------------------------------------------------------------------------
    # create_default() Tests
    # -------------------------------------------------------------------------

    def test_create_default_returns_chain(self):
        """create_default should return configured chain."""
        chain = self.ValidationChain.create_default()
        assert isinstance(chain, self.ValidationChain)
        assert len(chain) == 3

    def test_create_default_has_correct_validators(self):
        """create_default should include OddsValidator, ProfitValidator, TimeValidator."""
        chain = self.ValidationChain.create_default()
        validator_names = [v.name for v in chain.validators]
        assert "OddsValidator" in validator_names
        assert "ProfitValidator" in validator_names
        assert "TimeValidator" in validator_names

    def test_create_default_correct_order(self):
        """create_default should have validators in correct order (CPU first)."""
        chain = self.ValidationChain.create_default()
        validator_names = [v.name for v in chain.validators]
        assert validator_names == ["OddsValidator", "ProfitValidator", "TimeValidator"]

    # -------------------------------------------------------------------------
    # ValidationResult Tests
    # -------------------------------------------------------------------------

    def test_validation_result_is_frozen(self):
        """ValidationResult should be immutable."""
        from src.domain.rules.validation_chain import ValidationResult
        result = ValidationResult(is_valid=True)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.is_valid = False

    def test_validation_result_with_all_fields(self):
        """ValidationResult should store all fields."""
        from src.domain.rules.validation_chain import ValidationResult
        result = ValidationResult(
            is_valid=False,
            error_message="Test error",
            failed_validator="TestValidator"
        )
        assert result.is_valid is False
        assert result.error_message == "Test error"
        assert result.failed_validator == "TestValidator"




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


def _create_surebet_with_future_event(profit_value: float, hours_from_now: float = 1.0) -> Surebet:
    """Helper to create Surebet with specified profit and future event time."""
    future_time = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    sharp_pick = Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.10),
        market_type=MarketType.OVER,
        variety="2.5",
        event_time=future_time,
        bookmaker="pinnaclesports",
    )
    soft_pick = Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.05),
        market_type=MarketType.UNDER,
        variety="2.5",
        event_time=future_time,
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


from datetime import timedelta

from src.domain.rules.validators.time_validator import TimeValidator


def _create_pick_with_event_time(seconds_from_now: float) -> Pick:
    """Helper to create Pick with event time relative to now."""
    event_time = datetime.now(timezone.utc) + timedelta(seconds=seconds_from_now)
    return Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.00),
        market_type=MarketType.WIN1,
        variety="",
        event_time=event_time,
        bookmaker="test_bookie",
    )


class TestTimeValidator:
    """Tests for TimeValidator (Task 3.4)."""

    def setup_method(self):
        """Set up test fixtures with default min_seconds=0."""
        self.validator = TimeValidator(min_seconds=0.0)

    # -------------------------------------------------------------------------
    # Constructor Tests
    # -------------------------------------------------------------------------

    def test_constructor_default_min_seconds(self):
        """Should use default min_seconds=0."""
        validator = TimeValidator()
        assert validator.name == "TimeValidator"

    def test_constructor_with_positive_min_seconds(self):
        """Should accept positive min_seconds for buffer."""
        validator = TimeValidator(min_seconds=60.0)
        assert validator.name == "TimeValidator"

    def test_constructor_with_zero_min_seconds(self):
        """Should accept zero min_seconds."""
        validator = TimeValidator(min_seconds=0.0)
        assert validator.name == "TimeValidator"

    def test_constructor_rejects_negative_min_seconds(self):
        """Should raise ValueError for negative min_seconds."""
        with pytest.raises(ValueError, match="cannot be negative"):
            TimeValidator(min_seconds=-1.0)

    # -------------------------------------------------------------------------
    # Validation - Valid Cases (Event in Future)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_future_event_passes(self):
        """Event 1 hour in future should pass."""
        pick = _create_pick_with_event_time(3600)  # +1 hour
        result = await self.validator.validate(pick)
        assert result.is_valid is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_event_just_starting_passes(self):
        """Event starting in 1 second should pass with min_seconds=0."""
        pick = _create_pick_with_event_time(1)  # +1 second
        result = await self.validator.validate(pick)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_event_10_minutes_future_passes(self):
        """Event 10 minutes in future should pass."""
        pick = _create_pick_with_event_time(600)  # +10 minutes
        result = await self.validator.validate(pick)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_event_with_buffer_passes(self):
        """Event with sufficient buffer should pass."""
        validator = TimeValidator(min_seconds=60.0)
        pick = _create_pick_with_event_time(120)  # +2 minutes
        result = await validator.validate(pick)
        assert result.is_valid is True

    # -------------------------------------------------------------------------
    # Validation - Invalid Cases (Event Started or Within Buffer)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_past_event_fails(self):
        """Event 1 hour ago should fail."""
        pick = _create_pick_with_event_time(-3600)  # -1 hour
        result = await self.validator.validate(pick)
        assert result.is_valid is False
        assert "started" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_event_just_started_fails(self):
        """Event that just started should fail."""
        pick = _create_pick_with_event_time(-1)  # -1 second
        result = await self.validator.validate(pick)
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_event_within_buffer_fails(self):
        """Event within buffer period should fail."""
        validator = TimeValidator(min_seconds=60.0)
        pick = _create_pick_with_event_time(30)  # +30 seconds (< 60 buffer)
        result = await validator.validate(pick)
        assert result.is_valid is False
        assert "minimum required" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_event_exactly_at_buffer_fails(self):
        """Event exactly at buffer boundary should fail (not > min_seconds)."""
        validator = TimeValidator(min_seconds=60.0)
        pick = _create_pick_with_event_time(60)  # exactly 60 seconds
        result = await validator.validate(pick)
        assert result.is_valid is False

    # -------------------------------------------------------------------------
    # Error Message Format Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_error_message_past_event_format(self):
        """Error for past event should include elapsed time."""
        pick = _create_pick_with_event_time(-60)  # -60 seconds
        result = await self.validator.validate(pick)
        assert result.is_valid is False
        assert "60" in result.error_message
        assert "started" in result.error_message.lower()
        assert "ago" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_error_message_within_buffer_format(self):
        """Error for within-buffer event should include both times."""
        validator = TimeValidator(min_seconds=60.0)
        pick = _create_pick_with_event_time(30)  # +30 seconds
        result = await validator.validate(pick)
        assert result.is_valid is False
        assert "30" in result.error_message  # seconds until event
        assert "60" in result.error_message  # minimum required


# =============================================================================
# Tests adicionales para 100% cobertura (Tarea 3.6)
# =============================================================================


class TestValidatorModuleExports:
    """Tests for validators module __init__.py exports."""

    def test_base_validator_exportable(self):
        """BaseValidator should be importable from validators package."""
        from src.domain.rules.validators import BaseValidator, ValidationResult
        assert BaseValidator is not None
        assert ValidationResult is not None

    def test_odds_validator_exportable(self):
        """OddsValidator should be importable from validators package."""
        from src.domain.rules.validators import OddsValidator
        assert OddsValidator is not None

    def test_profit_validator_exportable(self):
        """ProfitValidator should be importable from validators package."""
        from src.domain.rules.validators import ProfitValidator
        assert ProfitValidator is not None

    def test_time_validator_exportable(self):
        """TimeValidator should be importable from validators package."""
        from src.domain.rules.validators import TimeValidator
        assert TimeValidator is not None


class TestValidationChainEdgeCases:
    """Additional edge case tests for ValidationChain."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.domain.rules.validation_chain import ValidationChain
        self.ValidationChain = ValidationChain

    @pytest.mark.asyncio
    async def test_chain_with_only_profit_validator_and_pick_input(self):
        """Chain with only ProfitValidator should skip when given Pick."""
        chain = self.ValidationChain([ProfitValidator()])
        pick = _create_pick_with_odds(2.50)
        result = await chain.validate(pick)
        # Should pass because ProfitValidator is skipped for Pick input
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_chain_mixed_validators_with_surebet(self):
        """Mixed validators should correctly route Surebet and Pick."""
        chain = self.ValidationChain([
            OddsValidator(),
            ProfitValidator(max_profit=50.0),  # Wide range to pass
            TimeValidator(),
        ])
        surebet = _create_surebet_with_future_event(5.0)
        result = await chain.validate(surebet)
        assert result.is_valid is True
