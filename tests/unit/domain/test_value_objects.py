"""Tests for value objects.

Test Requirements:
- Odds validation and immutability
- Profit validation and acceptable range
- MarketType opposite resolution

Reference:
- docs/05-Implementation.md: Tasks 1.2-1.4
"""

from dataclasses import FrozenInstanceError

import pytest

from src.domain.value_objects.odds import Odds
from src.shared.exceptions import InvalidOddsError


class TestOdds:
    """Tests for Odds value object."""

    # -------------------------------------------------------------------------
    # Valid Odds Creation
    # -------------------------------------------------------------------------

    def test_valid_odds_creation(self) -> None:
        """Valid odds should create successfully."""
        odds = Odds(2.05)
        assert odds.value == 2.05

    def test_minimum_valid_odds(self) -> None:
        """Minimum valid odds (1.01) should pass."""
        odds = Odds(1.01)
        assert odds.value == 1.01

    def test_maximum_valid_odds(self) -> None:
        """Maximum valid odds (1000) should pass."""
        odds = Odds(1000.0)
        assert odds.value == 1000.0

    # -------------------------------------------------------------------------
    # Invalid Odds (should raise InvalidOddsError)
    # -------------------------------------------------------------------------

    def test_odds_below_minimum_raises_error(self) -> None:
        """Odds below 1.01 should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds(0.99)

    def test_odds_above_maximum_raises_error(self) -> None:
        """Odds above 1000 should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds(1001)

    def test_negative_odds_raises_error(self) -> None:
        """Negative odds should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds(-1)

    def test_odds_one_exactly_raises_error(self) -> None:
        """Odds of exactly 1.0 should raise InvalidOddsError (below minimum)."""
        with pytest.raises(InvalidOddsError):
            Odds(1.0)

    def test_zero_odds_raises_error(self) -> None:
        """Zero odds should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds(0)

    # -------------------------------------------------------------------------
    # Implied Probability
    # -------------------------------------------------------------------------

    def test_implied_probability(self) -> None:
        """Implied probability should be 1/odds."""
        odds = Odds(2.0)
        assert odds.implied_probability == 0.5

    def test_implied_probability_high_odds(self) -> None:
        """Implied probability for high odds."""
        odds = Odds(10.0)
        assert odds.implied_probability == 0.1

    def test_implied_probability_minimum(self) -> None:
        """Implied probability at minimum odds (high probability)."""
        odds = Odds(1.01)
        assert pytest.approx(odds.implied_probability, rel=1e-4) == 1 / 1.01

    # -------------------------------------------------------------------------
    # is_in_range Method
    # -------------------------------------------------------------------------

    def test_is_in_range_true(self) -> None:
        """is_in_range should return True when odds are in range."""
        odds = Odds(5.0)
        assert odds.is_in_range(1.0, 10.0) is True

    def test_is_in_range_false_below(self) -> None:
        """is_in_range should return False when odds are below range."""
        odds = Odds(5.0)
        assert odds.is_in_range(6.0, 10.0) is False

    def test_is_in_range_false_above(self) -> None:
        """is_in_range should return False when odds are above range."""
        odds = Odds(5.0)
        assert odds.is_in_range(1.0, 4.0) is False

    def test_is_in_range_boundary_inclusive(self) -> None:
        """is_in_range should include boundaries."""
        odds = Odds(5.0)
        assert odds.is_in_range(5.0, 5.0) is True

    # -------------------------------------------------------------------------
    # from_probability Factory Method
    # -------------------------------------------------------------------------

    def test_from_probability(self) -> None:
        """from_probability should create Odds from valid probability."""
        odds = Odds.from_probability(0.5)
        assert odds.value == 2.0

    def test_from_probability_low(self) -> None:
        """from_probability with low probability (high odds)."""
        odds = Odds.from_probability(0.1)
        assert odds.value == 10.0

    def test_from_probability_zero_raises_error(self) -> None:
        """from_probability with zero should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds.from_probability(0)

    def test_from_probability_one_raises_error(self) -> None:
        """from_probability with 1 should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds.from_probability(1)

    def test_from_probability_negative_raises_error(self) -> None:
        """from_probability with negative should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds.from_probability(-0.5)

    def test_from_probability_greater_than_one_raises_error(self) -> None:
        """from_probability > 1 should raise InvalidOddsError."""
        with pytest.raises(InvalidOddsError):
            Odds.from_probability(1.5)

    # -------------------------------------------------------------------------
    # Immutability
    # -------------------------------------------------------------------------

    def test_odds_is_immutable(self) -> None:
        """Odds should be immutable (frozen dataclass)."""
        odds = Odds(2.0)
        with pytest.raises(FrozenInstanceError):
            odds.value = 3.0  # type: ignore[misc]

    # -------------------------------------------------------------------------
    # String and Float Representations
    # -------------------------------------------------------------------------

    def test_odds_str_format(self) -> None:
        """str(odds) should format to 2 decimal places."""
        odds = Odds(2.05)
        assert str(odds) == "2.05"

    def test_odds_str_rounds_correctly(self) -> None:
        """str(odds) should round correctly."""
        odds = Odds(2.054)
        assert str(odds) == "2.05"
        odds2 = Odds(2.056)
        assert str(odds2) == "2.06"

    def test_odds_float_conversion(self) -> None:
        """float(odds) should return the value."""
        odds = Odds(2.05)
        assert float(odds) == 2.05


class TestProfit:
    """Tests for Profit value object."""

    def test_valid_profit_creation(self):
        """Valid profit should create successfully."""
        # profit = Profit(2.5)
        # assert profit.value == 2.5
        raise NotImplementedError("Test not implemented")

    def test_acceptable_profit_positive(self):
        """Profit 2.5% should be acceptable."""
        # profit = Profit(2.5)
        # assert profit.is_acceptable()
        raise NotImplementedError("Test not implemented")

    def test_acceptable_profit_negative(self):
        """Profit -0.5% should be acceptable (within range)."""
        # profit = Profit(-0.5)
        # assert profit.is_acceptable()
        raise NotImplementedError("Test not implemented")

    def test_unacceptable_profit_too_low(self):
        """Profit -2% should not be acceptable."""
        # profit = Profit(-2.0)
        # assert not profit.is_acceptable()
        raise NotImplementedError("Test not implemented")

    def test_unacceptable_profit_too_high(self):
        """Profit 30% should not be acceptable."""
        # profit = Profit(30.0)
        # assert not profit.is_acceptable()
        raise NotImplementedError("Test not implemented")

    def test_profit_outside_absolute_range_raises_error(self):
        """Profit > 100% should raise InvalidProfitError."""
        # with pytest.raises(InvalidProfitError):
        #     Profit(150)
        raise NotImplementedError("Test not implemented")


class TestMarketType:
    """Tests for MarketType enum."""

    def test_win1_opposite_is_win2(self):
        """win1 opposite should be win2."""
        # market = MarketType.WIN1
        # opposites = market.get_opposites()
        # assert MarketType.WIN2 in opposites
        raise NotImplementedError("Test not implemented")

    def test_over_opposite_is_under(self):
        """over opposite should be under."""
        # market = MarketType.OVER
        # opposites = market.get_opposites()
        # assert MarketType.UNDER in opposites
        raise NotImplementedError("Test not implemented")

    def test_1x_has_multiple_opposites(self):
        """_1x should have _x2 and _12 as opposites."""
        # market = MarketType._1X
        # opposites = market.get_opposites()
        # assert MarketType._X2 in opposites
        # assert MarketType._12 in opposites
        raise NotImplementedError("Test not implemented")

    def test_from_string_case_insensitive(self):
        """from_string should be case insensitive."""
        # market = MarketType.from_string("OVER")
        # assert market == MarketType.OVER
        raise NotImplementedError("Test not implemented")
