"""Profit value object representing surebet profit percentage.

Implementation Requirements:
- Immutable dataclass (frozen=True)
- Validation: -100 <= profit <= 100
- Method: is_acceptable() -> bool (checks if within trading range)
- Trading range: -1% to 25% (from docs/01-SRS.md RF-003)

Reference:
- docs/04-Structure.md: "value_objects/"
- docs/05-Implementation.md: Task 1.3
- docs/02-PDR.md: Section 3.1.1 (Value Objects)
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.exceptions import InvalidProfitError


@dataclass(frozen=True)
class Profit:
    """Immutable value object representing profit percentage.

    Profit is stored as a percentage (e.g., 2.5 means 2.5%).

    Attributes:
        value: The profit percentage value.

    Note:
        ABSOLUTE_MIN/MAX are mathematical validity limits, NOT business rules.
        Business rules (e.g., only accept picks with profit -1% to 25%) are
        checked via is_acceptable() using MIN_ACCEPTABLE/MAX_ACCEPTABLE.

    Examples:
        >>> profit = Profit(2.5)
        >>> profit.value
        2.5
        >>> profit.is_acceptable()
        True
        >>> profit.as_decimal
        0.025
    """

    value: float

    # Mathematical validity limits (NOT business rules)
    # These define what is mathematically valid as profit percentage
    ABSOLUTE_MIN: float = -100.0  # Cannot lose more than 100%
    ABSOLUTE_MAX: float = 100.0   # Cannot gain more than 100% in surebet

    # Trading limits (from SRS RF-003)
    # These are business rules for acceptable trading range
    MIN_ACCEPTABLE: float = -1.0
    MAX_ACCEPTABLE: float = 25.0

    def __post_init__(self) -> None:
        """Validate profit is within mathematically valid range."""
        if not (self.ABSOLUTE_MIN <= self.value <= self.ABSOLUTE_MAX):
            raise InvalidProfitError(
                f"Profit {self.value}% outside valid range "
                f"[{self.ABSOLUTE_MIN}%, {self.ABSOLUTE_MAX}%]"
            )

    def __float__(self) -> float:
        """Allow using Profit as float."""
        return self.value

    def __str__(self) -> str:
        """Format profit as percentage with 2 decimal places."""
        return f"{self.value:.2f}%"

    def is_acceptable(self) -> bool:
        """Check if profit is within acceptable trading range.

        This method is used by ProfitValidator to check against business rules.
        A profit outside this range is mathematically valid but not suitable
        for trading.

        Returns:
            True if MIN_ACCEPTABLE <= value <= MAX_ACCEPTABLE.

        Reference: RF-003 in docs/01-SRS.md
        """
        return self.MIN_ACCEPTABLE <= self.value <= self.MAX_ACCEPTABLE

    @property
    def as_decimal(self) -> float:
        """Convert percentage to decimal.

        Returns:
            Profit as decimal (e.g., 0.025 for 2.5%).
        """
        return self.value / 100
