"""Odds value object representing betting odds.

Implementation Requirements:
- Immutable dataclass (frozen=True)
- Validation: 1.01 <= odds <= 1000.0
- Raise InvalidOddsError on invalid values
- Property: implied_probability -> float (returns 1/value)
- Method: is_in_range(min, max) -> bool

Reference:
- docs/04-Structure.md: "value_objects/"
- docs/05-Implementation.md: Task 1.2
- docs/02-PDR.md: Section 3.1.1 (Value Objects)
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.exceptions import InvalidOddsError


@dataclass(frozen=True)
class Odds:
    """Immutable value object representing betting odds.

    Odds must be within valid range (1.01 - 1000.0).

    Attributes:
        value: The decimal odds value.

    Note:
        ABSOLUTE_MIN/MAX are mathematical validity limits, NOT business rules.
        Business rules (e.g., only send picks with odds 1.10-9.99) are handled
        by OddsValidator using Settings.MIN_ODDS/MAX_ODDS from .env.

    Examples:
        >>> odds = Odds(2.05)
        >>> odds.value
        2.05
        >>> odds.implied_probability
        0.4878048780487805
        >>> odds.is_in_range(1.5, 3.0)
        True
    """

    value: float

    # Mathematical validity limits (NOT business rules from .env)
    # These define what is mathematically valid as betting odds
    ABSOLUTE_MIN: float = 1.01  # Minimum mathematically valid odds
    ABSOLUTE_MAX: float = 1000.0  # Maximum practical odds limit

    def __post_init__(self) -> None:
        """Validate odds are within mathematically valid range."""
        if not (self.ABSOLUTE_MIN <= self.value <= self.ABSOLUTE_MAX):
            raise InvalidOddsError(
                f"Odds {self.value} outside valid range "
                f"[{self.ABSOLUTE_MIN}, {self.ABSOLUTE_MAX}]"
            )

    def __float__(self) -> float:
        """Allow using Odds as float."""
        return self.value

    def __str__(self) -> str:
        """Format odds to 2 decimal places."""
        return f"{self.value:.2f}"

    @property
    def implied_probability(self) -> float:
        """Calculate implied probability from odds.

        Returns:
            Probability as decimal (e.g., 0.5 for odds 2.0).
        """
        return 1 / self.value

    def is_in_range(self, min_odds: float, max_odds: float) -> bool:
        """Check if odds are within specified range.

        This method is used by OddsValidator to check against business rules
        from Settings (MIN_ODDS/MAX_ODDS from .env).

        Args:
            min_odds: Minimum acceptable odds.
            max_odds: Maximum acceptable odds.

        Returns:
            True if min_odds <= value <= max_odds.
        """
        return min_odds <= self.value <= max_odds

    @classmethod
    def from_probability(cls, probability: float) -> Odds:
        """Create Odds from probability.

        Args:
            probability: Value between 0 and 1 (exclusive).

        Returns:
            Odds instance with value = 1/probability.

        Raises:
            InvalidOddsError: If probability is not in (0, 1).
        """
        if not (0 < probability < 1):
            raise InvalidOddsError(
                f"Probability {probability} must be between 0 and 1 (exclusive)"
            )
        return cls(1 / probability)
