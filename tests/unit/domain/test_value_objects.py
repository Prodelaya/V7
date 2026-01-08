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

from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds
from src.domain.value_objects.profit import Profit
from src.shared.exceptions import (
    InvalidMarketError,
    InvalidOddsError,
    InvalidProfitError,
)


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

    # -------------------------------------------------------------------------
    # Valid Profit Creation
    # -------------------------------------------------------------------------

    def test_valid_profit_creation(self) -> None:
        """Valid profit should create successfully."""
        profit = Profit(2.5)
        assert profit.value == 2.5

    def test_profit_boundary_absolute_min(self) -> None:
        """Minimum absolute profit (-100%) should pass."""
        profit = Profit(-100.0)
        assert profit.value == -100.0

    def test_profit_boundary_absolute_max(self) -> None:
        """Maximum absolute profit (100%) should pass."""
        profit = Profit(100.0)
        assert profit.value == 100.0

    def test_profit_zero(self) -> None:
        """Zero profit should be valid."""
        profit = Profit(0.0)
        assert profit.value == 0.0

    # -------------------------------------------------------------------------
    # Invalid Profit (should raise InvalidProfitError)
    # -------------------------------------------------------------------------

    def test_profit_outside_absolute_range_raises_error(self) -> None:
        """Profit > 100% should raise InvalidProfitError."""
        with pytest.raises(InvalidProfitError):
            Profit(150)

    def test_profit_negative_absolute_raises_error(self) -> None:
        """Profit < -100% should raise InvalidProfitError."""
        with pytest.raises(InvalidProfitError):
            Profit(-150)

    # -------------------------------------------------------------------------
    # is_acceptable Method (trading range -1% to 25%)
    # -------------------------------------------------------------------------

    def test_acceptable_profit_positive(self) -> None:
        """Profit 2.5% should be acceptable."""
        profit = Profit(2.5)
        assert profit.is_acceptable() is True

    def test_acceptable_profit_negative(self) -> None:
        """Profit -0.5% should be acceptable (within range)."""
        profit = Profit(-0.5)
        assert profit.is_acceptable() is True

    def test_acceptable_profit_zero(self) -> None:
        """Profit 0% should be acceptable."""
        profit = Profit(0.0)
        assert profit.is_acceptable() is True

    def test_profit_boundary_acceptable_min(self) -> None:
        """Profit -1% (boundary) should be acceptable."""
        profit = Profit(-1.0)
        assert profit.is_acceptable() is True

    def test_profit_boundary_acceptable_max(self) -> None:
        """Profit 25% (boundary) should be acceptable."""
        profit = Profit(25.0)
        assert profit.is_acceptable() is True

    def test_unacceptable_profit_too_low(self) -> None:
        """Profit -2% should not be acceptable."""
        profit = Profit(-2.0)
        assert profit.is_acceptable() is False

    def test_unacceptable_profit_too_high(self) -> None:
        """Profit 30% should not be acceptable."""
        profit = Profit(30.0)
        assert profit.is_acceptable() is False

    # -------------------------------------------------------------------------
    # as_decimal Property
    # -------------------------------------------------------------------------

    def test_profit_as_decimal(self) -> None:
        """as_decimal should convert percentage to decimal."""
        profit = Profit(2.5)
        assert profit.as_decimal == 0.025

    def test_profit_as_decimal_negative(self) -> None:
        """as_decimal should work with negative profit."""
        profit = Profit(-0.5)
        assert profit.as_decimal == -0.005

    # -------------------------------------------------------------------------
    # String and Float Representations
    # -------------------------------------------------------------------------

    def test_profit_str_format(self) -> None:
        """str(profit) should format with 2 decimals and %."""
        profit = Profit(2.5)
        assert str(profit) == "2.50%"

    def test_profit_str_rounds_correctly(self) -> None:
        """str(profit) should round correctly."""
        profit = Profit(2.555)
        assert str(profit) == "2.56%"

    def test_profit_float_conversion(self) -> None:
        """float(profit) should return the value."""
        profit = Profit(2.5)
        assert float(profit) == 2.5

    # -------------------------------------------------------------------------
    # Immutability
    # -------------------------------------------------------------------------

    def test_profit_is_immutable(self) -> None:
        """Profit should be immutable (frozen dataclass)."""
        profit = Profit(2.5)
        with pytest.raises(FrozenInstanceError):
            profit.value = 5.0  # type: ignore[misc]


class TestMarketType:
    """Tests for MarketType enum."""

    # -------------------------------------------------------------------------
    # Enum Values
    # -------------------------------------------------------------------------

    def test_market_type_win1_value(self) -> None:
        """WIN1 should have value 'win1'."""
        assert MarketType.WIN1.value == "win1"

    def test_market_type_win2_value(self) -> None:
        """WIN2 should have value 'win2'."""
        assert MarketType.WIN2.value == "win2"

    def test_market_type_over_value(self) -> None:
        """OVER should have value 'over'."""
        assert MarketType.OVER.value == "over"

    def test_market_type_under_value(self) -> None:
        """UNDER should have value 'under'."""
        assert MarketType.UNDER.value == "under"

    def test_all_values_are_lowercase(self) -> None:
        """All enum values should be lowercase strings."""
        for market in MarketType:
            assert market.value == market.value.lower(), f"{market.name} value is not lowercase"

    # -------------------------------------------------------------------------
    # get_opposites() - Symmetric 1:1 Markets
    # -------------------------------------------------------------------------

    def test_win1_opposite_is_win2(self) -> None:
        """win1 opposite should be win2."""
        opposites = MarketType.WIN1.get_opposites()
        assert len(opposites) == 1
        assert MarketType.WIN2 in opposites

    def test_win2_opposite_is_win1(self) -> None:
        """win2 opposite should be win1."""
        opposites = MarketType.WIN2.get_opposites()
        assert len(opposites) == 1
        assert MarketType.WIN1 in opposites

    def test_over_opposite_is_under(self) -> None:
        """over opposite should be under."""
        opposites = MarketType.OVER.get_opposites()
        assert len(opposites) == 1
        assert MarketType.UNDER in opposites

    def test_under_opposite_is_over(self) -> None:
        """under opposite should be over."""
        opposites = MarketType.UNDER.get_opposites()
        assert len(opposites) == 1
        assert MarketType.OVER in opposites

    def test_ah1_opposite_is_ah2(self) -> None:
        """ah1 opposite should be ah2."""
        opposites = MarketType.AH1.get_opposites()
        assert MarketType.AH2 in opposites

    def test_odd_opposite_is_even(self) -> None:
        """odd opposite should be even."""
        opposites = MarketType.ODD.get_opposites()
        assert MarketType.EVEN in opposites

    def test_yes_opposite_is_no(self) -> None:
        """yes opposite should be no."""
        opposites = MarketType.YES.get_opposites()
        assert MarketType.NO in opposites

    def test_eover_opposite_is_eunder(self) -> None:
        """eover opposite should be e_under."""
        opposites = MarketType.EOVER.get_opposites()
        assert MarketType.EUNDER in opposites

    def test_win1retx_opposite_is_win2retx(self) -> None:
        """win1retx opposite should be win2retx."""
        opposites = MarketType.WIN1RETX.get_opposites()
        assert MarketType.WIN2RETX in opposites

    def test_winonly1_opposite_is_winonly2(self) -> None:
        """winonly1 opposite should be winonly2."""
        opposites = MarketType.WINONLY1.get_opposites()
        assert MarketType.WINONLY2 in opposites

    def test_win1tonil_opposite_is_win2tonil(self) -> None:
        """win1tonil opposite should be win2tonil."""
        opposites = MarketType.WIN1TONIL.get_opposites()
        assert MarketType.WIN2TONIL in opposites

    def test_cleansheet1_opposite_is_cleansheet2(self) -> None:
        """clean_sheet_1 opposite should be clean_sheet_2."""
        opposites = MarketType.CLEAN_SHEET_1.get_opposites()
        assert MarketType.CLEAN_SHEET_2 in opposites

    def test_win1qualify_opposite_is_win2qualify(self) -> None:
        """win1 qualify opposite should be win2 qualify."""
        opposites = MarketType.WIN1_QUALIFY.get_opposites()
        assert MarketType.WIN2_QUALIFY in opposites

    def test_betweenmarginh1_opposite_is_betweenmarginh2(self) -> None:
        """BETWEENMARGINH1 opposite should be BETWEENMARGINH2."""
        opposites = MarketType.BETWEENMARGINH1.get_opposites()
        assert MarketType.BETWEENMARGINH2 in opposites

    # -------------------------------------------------------------------------
    # get_opposites() - Multiple Opposites (Double Chance)
    # -------------------------------------------------------------------------

    def test_1x_has_multiple_opposites(self) -> None:
        """_1x should have _x2 and _12 as opposites."""
        opposites = MarketType._1X.get_opposites()
        assert len(opposites) == 2
        assert MarketType._X2 in opposites
        assert MarketType._12 in opposites

    def test_x2_has_multiple_opposites(self) -> None:
        """_x2 should have _1x and _12 as opposites."""
        opposites = MarketType._X2.get_opposites()
        assert len(opposites) == 2
        assert MarketType._1X in opposites
        assert MarketType._12 in opposites

    def test_12_has_multiple_opposites(self) -> None:
        """_12 should have _1x and _x2 as opposites."""
        opposites = MarketType._12.get_opposites()
        assert len(opposites) == 2
        assert MarketType._1X in opposites
        assert MarketType._X2 in opposites

    # -------------------------------------------------------------------------
    # get_opposites() - No Opposites
    # -------------------------------------------------------------------------

    def test_draw_has_no_opposites(self) -> None:
        """draw should have no opposites."""
        opposites = MarketType.DRAW.get_opposites()
        assert opposites == []

    # -------------------------------------------------------------------------
    # get_opposites() - Symmetry Property
    # -------------------------------------------------------------------------

    def test_opposite_symmetry(self) -> None:
        """If A is opposite of B, then B must be opposite of A."""
        for market in MarketType:
            for opposite in market.get_opposites():
                assert market in opposite.get_opposites(), (
                    f"Symmetry broken: {market.name} -> {opposite.name} but not vice versa"
                )

    # -------------------------------------------------------------------------
    # get_opposites() - Returns New List (Immutability)
    # -------------------------------------------------------------------------

    def test_get_opposites_returns_new_list(self) -> None:
        """get_opposites should return a new list each time."""
        result1 = MarketType.WIN1.get_opposites()
        result2 = MarketType.WIN1.get_opposites()
        assert result1 is not result2  # Different objects
        assert result1 == result2  # Same content

    # -------------------------------------------------------------------------
    # from_string() - Valid Cases
    # -------------------------------------------------------------------------

    def test_from_string_exact_match(self) -> None:
        """from_string should match exact value."""
        assert MarketType.from_string("win1") == MarketType.WIN1

    def test_from_string_case_insensitive_upper(self) -> None:
        """from_string should be case insensitive (uppercase)."""
        assert MarketType.from_string("OVER") == MarketType.OVER

    def test_from_string_case_insensitive_mixed(self) -> None:
        """from_string should be case insensitive (mixed case)."""
        assert MarketType.from_string("Win1") == MarketType.WIN1

    def test_from_string_with_leading_whitespace(self) -> None:
        """from_string should strip leading whitespace."""
        assert MarketType.from_string("  win1") == MarketType.WIN1

    def test_from_string_with_trailing_whitespace(self) -> None:
        """from_string should strip trailing whitespace."""
        assert MarketType.from_string("win1  ") == MarketType.WIN1

    def test_from_string_with_both_whitespace(self) -> None:
        """from_string should strip both sides whitespace."""
        assert MarketType.from_string("  over  ") == MarketType.OVER

    def test_from_string_underscore_prefix(self) -> None:
        """from_string should handle underscore-prefixed values."""
        assert MarketType.from_string("_1x") == MarketType._1X

    def test_from_string_with_space_in_value(self) -> None:
        """from_string should handle values with spaces."""
        assert MarketType.from_string("win1 qualify") == MarketType.WIN1_QUALIFY

    # -------------------------------------------------------------------------
    # from_string() - Unknown Markets (UNKNOWN fallback)
    # -------------------------------------------------------------------------

    def test_from_string_unknown_returns_unknown(self) -> None:
        """from_string should return UNKNOWN for unrecognized markets."""
        result = MarketType.from_string("xyz_unknown_market")
        assert result == MarketType.UNKNOWN

    def test_from_string_unknown_logs_warning(self, caplog) -> None:
        """from_string should log warning for unknown markets."""
        import logging
        with caplog.at_level(logging.WARNING):
            MarketType.from_string("new_market_type")
        assert "Unknown market type" in caplog.text
        assert "new_market_type" in caplog.text

    def test_unknown_has_no_opposites(self) -> None:
        """UNKNOWN market should have no opposites."""
        assert MarketType.UNKNOWN.get_opposites() == []

    def test_unknown_has_opposites_false(self) -> None:
        """UNKNOWN market has_opposites should return False."""
        assert MarketType.UNKNOWN.has_opposites() is False

    # -------------------------------------------------------------------------
    # from_string() - Strict Mode
    # -------------------------------------------------------------------------

    def test_from_string_strict_raises_error(self) -> None:
        """from_string with strict=True should raise InvalidMarketError for unknown markets."""
        with pytest.raises(InvalidMarketError):
            MarketType.from_string("unknown_market", strict=True)

    def test_from_string_strict_valid_market(self) -> None:
        """from_string with strict=True should work for valid markets."""
        assert MarketType.from_string("win1", strict=True) == MarketType.WIN1

    # -------------------------------------------------------------------------
    # from_string() - Empty/Whitespace (always raises)
    # -------------------------------------------------------------------------

    def test_from_string_empty_raises_error(self) -> None:
        """from_string should raise InvalidMarketError for empty string."""
        with pytest.raises(InvalidMarketError):
            MarketType.from_string("")

    def test_from_string_whitespace_only_raises_error(self) -> None:
        """from_string should raise InvalidMarketError for whitespace only."""
        with pytest.raises(InvalidMarketError):
            MarketType.from_string("   ")

    # -------------------------------------------------------------------------
    # has_opposites() Method
    # -------------------------------------------------------------------------

    def test_has_opposites_true_for_win1(self) -> None:
        """has_opposites should return True for WIN1."""
        assert MarketType.WIN1.has_opposites() is True

    def test_has_opposites_true_for_double_chance(self) -> None:
        """has_opposites should return True for double chance markets."""
        assert MarketType._1X.has_opposites() is True

    def test_has_opposites_false_for_draw(self) -> None:
        """has_opposites should return False for DRAW."""
        assert MarketType.DRAW.has_opposites() is False

    # -------------------------------------------------------------------------
    # is_opposite_of() Method
    # -------------------------------------------------------------------------

    def test_is_opposite_of_true(self) -> None:
        """is_opposite_of should return True for actual opposites."""
        assert MarketType.WIN1.is_opposite_of(MarketType.WIN2) is True

    def test_is_opposite_of_false(self) -> None:
        """is_opposite_of should return False for non-opposites."""
        assert MarketType.WIN1.is_opposite_of(MarketType.OVER) is False

    def test_is_opposite_of_self_false(self) -> None:
        """is_opposite_of should return False for self."""
        assert MarketType.WIN1.is_opposite_of(MarketType.WIN1) is False

    def test_is_opposite_of_multiple(self) -> None:
        """is_opposite_of should work with multiple opposites."""
        assert MarketType._1X.is_opposite_of(MarketType._X2) is True
        assert MarketType._1X.is_opposite_of(MarketType._12) is True

    # -------------------------------------------------------------------------
    # Legacy Compatibility
    # -------------------------------------------------------------------------

    def test_opposite_markets_dict_exists(self) -> None:
        """OPPOSITE_MARKETS dict should exist for legacy compatibility."""
        from src.domain.value_objects.market_type import OPPOSITE_MARKETS
        assert isinstance(OPPOSITE_MARKETS, dict)
        assert len(OPPOSITE_MARKETS) > 0

    def test_opposite_markets_dict_values_are_lists(self) -> None:
        """OPPOSITE_MARKETS values should be lists of strings."""
        from src.domain.value_objects.market_type import OPPOSITE_MARKETS
        for key, value in OPPOSITE_MARKETS.items():
            assert isinstance(key, str), f"Key {key} is not a string"
            assert isinstance(value, list), f"Value for {key} is not a list"
            for item in value:
                assert isinstance(item, str), f"Item {item} in {key} is not a string"

    def test_opposite_markets_contains_win1(self) -> None:
        """OPPOSITE_MARKETS should contain win1 -> [win2]."""
        from src.domain.value_objects.market_type import OPPOSITE_MARKETS
        assert "win1" in OPPOSITE_MARKETS
        assert "win2" in OPPOSITE_MARKETS["win1"]
