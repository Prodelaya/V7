"""Base calculator interface and result dataclasses.

Implements Strategy Pattern for sharp-specific stake and min_odds calculations.
Calculators receive profit limits via Dependency Injection to support .env config.

Design Decisions:
- Profit limits are injected, NOT hardcoded (configurable via .env)
- Each sharp bookmaker can have its own calculator implementation
- Formulas are documented with ADR references

Reference:
- docs/02-PDR.md: Section 4.1 (Strategy Pattern)
- docs/05-Implementation.md: Task 2.1
- docs/03-ADRs.md: ADR-002, ADR-003
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple

# Default profit limits (can be overridden via Settings/.env)
DEFAULT_MIN_PROFIT: float = -1.0
DEFAULT_MAX_PROFIT: float = 25.0


@dataclass(frozen=True, slots=True)
class StakeResult:
    """
    Result of stake calculation.

    Attributes:
        emoji: Stake indicator emoji (🔴, 🟠, 🟡, 🟢)
        confidence: Confidence level (0.0 - 1.0)
        units_suggestion: Tuple of (min, recommended, max) units

    Reference: RF-005 in docs/01-SRS.md
    """

    emoji: str
    confidence: float
    units_suggestion: Tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class MinOddsResult:
    """
    Result of minimum odds calculation.

    Attributes:
        min_odds: Minimum acceptable odds in soft bookmaker
        profit_threshold: Profit threshold used (e.g., -0.01 for -1%)

    Reference: RF-006 in docs/01-SRS.md
    """

    min_odds: float
    profit_threshold: float


class BaseCalculator(ABC):
    """
    Abstract base class for sharp-specific calculators.

    Implements Strategy Pattern - each sharp bookmaker has its own
    calculator with specific formulas and ranges.

    Profit limits are received via __init__ (Dependency Injection) to allow
    configuration via .env files. This avoids hardcoding business rules.

    Args:
        min_profit: Minimum acceptable profit % (default from .env: -1.0)
        max_profit: Maximum acceptable profit % (default from .env: 25.0)

    Example:
        >>> # In application layer, inject from Settings
        >>> settings = Settings.from_env()
        >>> calculator = PinnacleCalculator(
        ...     min_profit=settings.validation.min_profit,
        ...     max_profit=settings.validation.max_profit
        ... )

    Reference:
        - ADR-002 in docs/03-ADRs.md (Strategy Pattern)
        - ADR-003 in docs/03-ADRs.md (CORRECT min_odds formula)
    """

    def __init__(
        self,
        min_profit: float = DEFAULT_MIN_PROFIT,
        max_profit: float = DEFAULT_MAX_PROFIT,
    ) -> None:
        """
        Initialize calculator with configurable profit limits.

        Args:
            min_profit: Minimum acceptable profit % (default: -1.0)
            max_profit: Maximum acceptable profit % (default: 25.0)

        Raises:
            ValueError: If min_profit >= max_profit
        """
        if min_profit >= max_profit:
            raise ValueError(
                f"min_profit ({min_profit}) must be less than max_profit ({max_profit})"
            )
        self._min_profit = min_profit
        self._max_profit = max_profit

    @property
    def min_profit(self) -> float:
        """Minimum acceptable profit percentage."""
        return self._min_profit

    @property
    def max_profit(self) -> float:
        """Maximum acceptable profit percentage."""
        return self._max_profit

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Identifier for this calculator's sharp bookmaker.

        Returns:
            Bookmaker name (e.g., "pinnaclesports")
        """
        pass

    @abstractmethod
    def calculate_stake(self, profit: float) -> Optional[StakeResult]:
        """
        Calculate recommended stake based on surebet profit.

        Args:
            profit: Surebet profit percentage (e.g., 2.5 means 2.5%)

        Returns:
            StakeResult with emoji and units, or None if profit out of range

        Reference: RF-005 in docs/01-SRS.md

        Ranges for Pinnacle (from SRS):
            | Profit       | Emoji | Confidence |
            |--------------|-------|------------|
            | -1% to -0.5% | 🔴    | Low        |
            | -0.5% to 1.5%| 🟠    | Medium-low |
            | 1.5% to 4%   | 🟡    | Medium-high|
            | >4%          | 🟢    | High       |
        """
        pass

    @abstractmethod
    def calculate_min_odds(self, sharp_odds: float) -> MinOddsResult:
        """
        Calculate minimum acceptable odds in soft bookmaker.

        This is the lowest odds at which we still have acceptable value
        (typically -1% profit threshold).

        Args:
            sharp_odds: Odds of OPPOSITE market in sharp bookmaker

        Returns:
            MinOddsResult with minimum odds value

        Reference:
            - RF-006 in docs/01-SRS.md
            - ADR-003 in docs/03-ADRs.md (CORRECT formula)

        ⚠️ CORRECT Formula (from ADR-003):
            min_odds = 1 / (1.01 - 1/sharp_odds)

        ❌ WRONG Formula (from legacy V6 - DO NOT USE):
            oddmin = 1 / (margin - prob_contraria - (1/100))
        """
        pass

    def is_valid_profit(self, profit: float) -> bool:
        """
        Check if profit is within acceptable range.

        Uses the injected min_profit and max_profit limits
        (configurable via .env).

        Args:
            profit: Surebet profit percentage

        Returns:
            True if min_profit <= profit <= max_profit
        """
        return self._min_profit <= profit <= self._max_profit
