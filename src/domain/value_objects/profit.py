"""Profit value object representing surebet profit percentage.

Design Decisions:
- Immutable dataclass (frozen=True)
- Only validates MATHEMATICAL limits (-100% to 100%)
- BUSINESS limits (e.g., -1% to 25%) are NOT hardcoded here
- Business limits should come from Settings/.env for configurability

Reference:
- docs/04-Structure.md: "value_objects/"
- docs/05-Implementation.md: Task 1.3
- docs/02-PDR.md: Section 3.1.1 (Value Objects)
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.exceptions import InvalidProfitError

# Default trading limits (can be overridden via Settings/.env)
# These are only used as DEFAULTS, not hardcoded limits
DEFAULT_MIN_ACCEPTABLE: float = -1.0
DEFAULT_MAX_ACCEPTABLE: float = 25.0


@dataclass(frozen=True)
class Profit:
    """Immutable value object representing profit percentage.

    Profit is stored as a percentage (e.g., 2.5 means 2.5%).

    Attributes:
        value: The profit percentage value.

    Design Note:
        ABSOLUTE_MIN/MAX are mathematical validity limits, NOT business rules.
        Business rules (e.g., only accept picks with profit -1% to 25%) should
        be passed as parameters to is_acceptable() from Settings/.env.

    Examples:
        >>> profit = Profit(2.5)
        >>> profit.value
        2.5
        >>> profit.is_acceptable()  # Uses defaults
        True
        >>> profit.is_acceptable(min_profit=-0.5, max_profit=10.0)  # Custom limits
        True
        >>> profit.as_decimal
        0.025
    """

    value: float

    # Mathematical validity limits (NOT business rules)
    # These define what is mathematically valid as profit percentage
    # A profit cannot be less than -100% (total loss) or more than +100%
    ABSOLUTE_MIN: float = -100.0
    ABSOLUTE_MAX: float = 100.0

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

    def is_acceptable(
        self,
        min_profit: float = DEFAULT_MIN_ACCEPTABLE,
        max_profit: float = DEFAULT_MAX_ACCEPTABLE,
    ) -> bool:
        """Check if profit is within acceptable trading range.

        The limits should be passed in from Settings/.env for configurability.
        Default values are provided only for backwards compatibility.

        Args:
            min_profit: Minimum acceptable profit % (default: -1.0, from .env)
            max_profit: Maximum acceptable profit % (default: 25.0, from .env)

        Returns:
            True if min_profit <= value <= max_profit.

        Example:
            >>> profit = Profit(2.5)
            >>> # With defaults from .env
            >>> profit.is_acceptable()
            True
            >>> # With custom limits (e.g., for different subscription tier)
            >>> profit.is_acceptable(min_profit=0.0, max_profit=10.0)
            True

        Reference: RF-003 in docs/01-SRS.md
        """
        return min_profit <= self.value <= max_profit

    @property
    def as_decimal(self) -> float:
        """Convert percentage to decimal.

        Returns:
            Profit as decimal (e.g., 0.025 for 2.5%).
        """
        return self.value / 100
