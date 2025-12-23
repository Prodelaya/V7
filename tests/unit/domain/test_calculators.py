"""Tests for stake and min_odds calculators.

Test Requirements:
- PinnacleCalculator.calculate_stake() for each profit range
- PinnacleCalculator.calculate_min_odds() with reference values
- CalculatorFactory.get_calculator() returns correct type

Reference:
- docs/05-Implementation.md: Task 2.5
- docs/03-ADRs.md: ADR-003 (correct min_odds formula)
- docs/01-SRS.md: Appendix 6.2 (reference values)
"""

import pytest

from src.domain.services.calculators import (
    DEFAULT_MAX_PROFIT,
    DEFAULT_MIN_PROFIT,
    BaseCalculator,
    CalculatorFactory,
    MinOddsResult,
    PinnacleCalculator,
    StakeResult,
)


class TestPinnacleCalculator:
    """Tests for PinnacleCalculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = PinnacleCalculator()

    # ═══════════════════════════════════════════════════════════════════════════
    # STAKE CALCULATION TESTS (SRS RF-005)
    # ═══════════════════════════════════════════════════════════════════════════

    def test_calculate_stake_low_profit_returns_red_emoji(self):
        """Profit -0.8% should return 🔴."""
        result = self.calculator.calculate_stake(-0.8)
        assert result is not None
        assert result.emoji == "🔴"

    def test_calculate_stake_medium_low_profit_returns_orange_emoji(self):
        """Profit 0.5% should return 🟠."""
        result = self.calculator.calculate_stake(0.5)
        assert result is not None
        assert result.emoji == "🟠"

    def test_calculate_stake_medium_high_profit_returns_yellow_emoji(self):
        """Profit 2.5% should return 🟡."""
        result = self.calculator.calculate_stake(2.5)
        assert result is not None
        assert result.emoji == "🟡"

    def test_calculate_stake_high_profit_returns_green_emoji(self):
        """Profit 5% should return 🟢."""
        result = self.calculator.calculate_stake(5.0)
        assert result is not None
        assert result.emoji == "🟢"

    def test_calculate_stake_below_minimum_returns_none(self):
        """Profit -2% (below -1%) should return None."""
        result = self.calculator.calculate_stake(-2.0)
        assert result is None

    def test_calculate_stake_above_maximum_returns_none(self):
        """Profit 30% (above 25%) should return None."""
        result = self.calculator.calculate_stake(30.0)
        assert result is None

    def test_calculate_stake_boundary_minimum(self):
        """Profit exactly -1% should return 🔴."""
        result = self.calculator.calculate_stake(-1.0)
        assert result is not None
        assert result.emoji == "🔴"

    def test_calculate_stake_boundary_maximum(self):
        """Profit exactly 25% should return 🟢."""
        result = self.calculator.calculate_stake(25.0)
        assert result is not None
        assert result.emoji == "🟢"

    def test_calculate_stake_returns_stake_result(self):
        """Result should be a StakeResult dataclass with only emoji."""
        result = self.calculator.calculate_stake(2.0)
        assert isinstance(result, StakeResult)
        assert hasattr(result, "emoji")

    # ═══════════════════════════════════════════════════════════════════════════
    # MIN ODDS CALCULATION TESTS (ADR-003, Appendix 6.2)
    # Using CORRECT formula: min_odds = 1 / (1.01 - 1/sharp_odds)
    # ═══════════════════════════════════════════════════════════════════════════

    def test_calculate_min_odds_sharp_150(self):
        """Sharp odds 1.50 → min soft ~2.92."""
        result = self.calculator.calculate_min_odds(1.50)
        assert abs(result.min_odds - 2.92) < 0.05

    def test_calculate_min_odds_sharp_180(self):
        """Sharp odds 1.80 → min soft ~2.20."""
        result = self.calculator.calculate_min_odds(1.80)
        assert abs(result.min_odds - 2.20) < 0.05

    def test_calculate_min_odds_sharp_200(self):
        """Sharp odds 2.00 → min soft ~1.96."""
        result = self.calculator.calculate_min_odds(2.00)
        assert abs(result.min_odds - 1.96) < 0.05

    def test_calculate_min_odds_sharp_205(self):
        """Sharp odds 2.05 → min soft ~1.92."""
        result = self.calculator.calculate_min_odds(2.05)
        assert abs(result.min_odds - 1.92) < 0.05

    def test_calculate_min_odds_sharp_250(self):
        """Sharp odds 2.50 → min soft ~1.64."""
        result = self.calculator.calculate_min_odds(2.50)
        assert abs(result.min_odds - 1.64) < 0.05

    def test_calculate_min_odds_sharp_300(self):
        """Sharp odds 3.00 → min soft ~1.48."""
        result = self.calculator.calculate_min_odds(3.00)
        assert abs(result.min_odds - 1.48) < 0.05

    def test_calculate_min_odds_returns_min_odds_result(self):
        """Result should be a MinOddsResult dataclass."""
        result = self.calculator.calculate_min_odds(2.0)
        assert isinstance(result, MinOddsResult)
        assert hasattr(result, "min_odds")
        assert hasattr(result, "profit_threshold")

    def test_calculate_min_odds_profit_threshold(self):
        """Profit threshold should be -0.01 (-1%)."""
        result = self.calculator.calculate_min_odds(2.0)
        assert result.profit_threshold == -0.01

    # ═══════════════════════════════════════════════════════════════════════════
    # PROFIT VALIDATION TESTS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_is_valid_profit_within_range(self):
        """Profit within range should be valid."""
        assert self.calculator.is_valid_profit(2.5) is True
        assert self.calculator.is_valid_profit(0.0) is True
        assert self.calculator.is_valid_profit(-0.5) is True

    def test_is_valid_profit_below_minimum(self):
        """Profit below minimum should be invalid."""
        assert self.calculator.is_valid_profit(-2.0) is False

    def test_is_valid_profit_above_maximum(self):
        """Profit above maximum should be invalid."""
        assert self.calculator.is_valid_profit(30.0) is False

    def test_is_valid_profit_boundary_values(self):
        """Boundary values should be valid."""
        assert self.calculator.is_valid_profit(-1.0) is True
        assert self.calculator.is_valid_profit(25.0) is True

    # ═══════════════════════════════════════════════════════════════════════════
    # DEPENDENCY INJECTION TESTS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_default_limits(self):
        """Default calculator should have standard limits."""
        assert self.calculator.min_profit == DEFAULT_MIN_PROFIT
        assert self.calculator.max_profit == DEFAULT_MAX_PROFIT

    def test_custom_limits(self):
        """Calculator with custom limits should use those limits."""
        custom_calc = PinnacleCalculator(min_profit=-0.5, max_profit=15.0)
        assert custom_calc.min_profit == -0.5
        assert custom_calc.max_profit == 15.0

    def test_custom_limits_affect_validation(self):
        """Custom limits should affect is_valid_profit."""
        custom_calc = PinnacleCalculator(min_profit=-0.5, max_profit=15.0)
        # -0.8 is valid with default limits but invalid with custom
        assert self.calculator.is_valid_profit(-0.8) is True
        assert custom_calc.is_valid_profit(-0.8) is False

    def test_custom_limits_affect_stake_calculation(self):
        """Custom limits should affect calculate_stake."""
        custom_calc = PinnacleCalculator(min_profit=-0.5, max_profit=15.0)
        # -0.8 returns stake with default, None with custom
        assert self.calculator.calculate_stake(-0.8) is not None
        assert custom_calc.calculate_stake(-0.8) is None

    def test_name_property(self):
        """Name should return 'pinnaclesports'."""
        assert self.calculator.name == "pinnaclesports"


class TestCalculatorFactory:
    """Tests for CalculatorFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = CalculatorFactory()

    def test_get_pinnacle_calculator(self):
        """Factory returns PinnacleCalculator for 'pinnaclesports'."""
        calculator = self.factory.get_calculator("pinnaclesports")
        assert isinstance(calculator, PinnacleCalculator)

    def test_get_calculator_case_insensitive(self):
        """Factory handles case variations."""
        calc1 = self.factory.get_calculator("PinnacleSports")
        calc2 = self.factory.get_calculator("PINNACLESPORTS")
        calc3 = self.factory.get_calculator("pinnaclesports")
        assert isinstance(calc1, PinnacleCalculator)
        assert isinstance(calc2, PinnacleCalculator)
        assert isinstance(calc3, PinnacleCalculator)

    def test_get_unknown_returns_default(self):
        """Factory returns default for unknown bookmaker."""
        calculator = self.factory.get_calculator("unknown_bookie")
        assert calculator is not None
        assert isinstance(calculator, BaseCalculator)

    def test_factory_injects_default_limits(self):
        """Factory should inject default limits."""
        calc = self.factory.get_calculator("pinnaclesports")
        assert calc.min_profit == DEFAULT_MIN_PROFIT
        assert calc.max_profit == DEFAULT_MAX_PROFIT

    def test_factory_with_custom_limits(self):
        """Factory with custom limits passes them to calculators."""
        custom_factory = CalculatorFactory(min_profit=-0.5, max_profit=10.0)
        calc = custom_factory.get_calculator("pinnaclesports")
        assert calc.min_profit == -0.5
        assert calc.max_profit == 10.0

    def test_register_custom_calculator(self):
        """Factory can register custom calculators."""
        custom_calc = PinnacleCalculator(min_profit=0.0, max_profit=5.0)
        self.factory.register("custom_sharp", custom_calc)
        retrieved = self.factory.get_calculator("custom_sharp")
        assert retrieved is custom_calc

    def test_partial_match(self):
        """Factory matches partial bookmaker names."""
        calc = self.factory.get_calculator("pinnacle")
        assert isinstance(calc, PinnacleCalculator)


class TestStakeResultDataclass:
    """Tests for StakeResult dataclass."""

    def test_stake_result_is_frozen(self):
        """StakeResult should be immutable."""
        result = StakeResult("🟡")
        with pytest.raises(AttributeError):
            result.emoji = "🔴"  # type: ignore

    def test_stake_result_has_slots(self):
        """StakeResult should use __slots__ for memory efficiency."""
        result = StakeResult("🟡")
        with pytest.raises(AttributeError):
            result.__dict__  # noqa: B018


class TestMinOddsResultDataclass:
    """Tests for MinOddsResult dataclass."""

    def test_min_odds_result_is_frozen(self):
        """MinOddsResult should be immutable."""
        result = MinOddsResult(1.92, -0.01)
        with pytest.raises(AttributeError):
            result.min_odds = 2.0  # type: ignore

    def test_min_odds_result_has_slots(self):
        """MinOddsResult should use __slots__ for memory efficiency."""
        result = MinOddsResult(1.92, -0.01)
        with pytest.raises(AttributeError):
            result.__dict__  # noqa: B018


class TestValidationDefensive:
    """Tests for defensive validations."""

    def test_min_profit_greater_than_max_profit_raises_error(self):
        """Creating calculator with min >= max should raise ValueError."""
        with pytest.raises(ValueError, match="must be less than"):
            PinnacleCalculator(min_profit=25.0, max_profit=-1.0)

    def test_min_profit_equal_to_max_profit_raises_error(self):
        """Creating calculator with min == max should raise ValueError."""
        with pytest.raises(ValueError, match="must be less than"):
            PinnacleCalculator(min_profit=5.0, max_profit=5.0)

    def test_sharp_odds_below_one_raises_error(self):
        """Sharp odds <= 1.0 should raise ValueError."""
        calc = PinnacleCalculator()
        with pytest.raises(ValueError, match="must be > 1.0"):
            calc.calculate_min_odds(0.95)

    def test_sharp_odds_equal_one_raises_error(self):
        """Sharp odds == 1.0 should raise ValueError."""
        calc = PinnacleCalculator()
        with pytest.raises(ValueError, match="must be > 1.0"):
            calc.calculate_min_odds(1.0)


class TestCalculationService:
    """Tests for CalculationService."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.domain.services import CalculationService

        self.service = CalculationService()

    def test_calculate_stake_delegates_to_calculator(self):
        """Service should delegate to correct calculator."""
        result = self.service.calculate_stake(2.5, "pinnaclesports")
        assert result is not None
        assert result.emoji == "🟡"

    def test_calculate_min_odds_delegates_to_calculator(self):
        """Service should delegate to correct calculator."""
        result = self.service.calculate_min_odds(2.05, "pinnaclesports")
        assert abs(result.min_odds - 1.92) < 0.05

    def test_calculate_stake_with_unknown_bookmaker_uses_default(self):
        """Unknown bookmaker should use default (Pinnacle)."""
        result = self.service.calculate_stake(2.5, "unknown_bookie")
        assert result is not None
        assert result.emoji == "🟡"

    def test_service_with_custom_factory(self):
        """Service should accept custom factory."""
        from src.domain.services import CalculationService

        custom_factory = CalculatorFactory(min_profit=-0.5, max_profit=10.0)
        service = CalculationService(calculator_factory=custom_factory)
        # -0.8 should be rejected with custom limits
        result = service.calculate_stake(-0.8, "pinnaclesports")
        assert result is None
