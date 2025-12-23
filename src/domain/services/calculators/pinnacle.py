"""Pinnacle-specific calculator implementation.

Implements BaseCalculator for Pinnacle Sports as the sharp bookmaker reference.
Uses the CORRECT min_odds formula from ADR-003.

Design Decisions:
- Profit limits are inherited from BaseCalculator (injected via .env)
- Stake ranges are based on relative positions within the profit range
- Min odds formula uses exact -1% profit threshold

Reference:
- docs/02-PDR.md: Section 4.1 (Strategy Pattern)
- docs/05-Implementation.md: Task 2.2
- docs/03-ADRs.md: ADR-003 (CORRECT formula)
- docs/01-SRS.md: RF-005, RF-006, Appendix 6.2
"""

from typing import Optional

from .base import BaseCalculator, MinOddsResult, StakeResult


class PinnacleCalculator(BaseCalculator):
    """
    Calculator strategy for Pinnacle Sports as sharp bookmaker.

    Pinnacle is considered the market reference due to:
    - Low margins (~2-3%)
    - Winners accepted policy
    - Efficient odds that reflect true probabilities

    Stake ranges (from docs/01-SRS.md RF-005):
        | Profit       | Emoji | Confidence |
        |--------------|-------|------------|
        | -1% to -0.5% | 🔴    | Low        |
        | -0.5% to 1.5%| 🟠    | Medium-low |
        | 1.5% to 4%   | 🟡    | Medium-high|
        | >4%          | 🟢    | High       |

    Min odds formula (from docs/03-ADRs.md ADR-003):
        min_odds = 1 / (1.01 - 1/sharp_odds)

    Reference table (from docs/01-SRS.md Appendix 6.2):
        | Sharp Odds | Min Soft Odds |
        |------------|---------------|
        | 1.50       | 2.92          |
        | 1.80       | 2.20          |
        | 2.00       | 1.96          |
        | 2.05       | 1.92          |
        | 2.50       | 1.64          |
        | 3.00       | 1.48          |
    """

    # Profit threshold for min_odds calculation (as decimal, -1%)
    PROFIT_THRESHOLD: float = -0.01

    # Stake ranges: (min_profit, max_profit, emoji)
    # Simple mapping from profit range to visual indicator
    STAKE_RANGES = (
        (-1.0, -0.5, "🔴"),  # Low profit - caution
        (-0.5, 1.5, "🟠"),  # Medium-low profit
        (1.5, 4.0, "🟡"),  # Medium-high profit
        (4.0, 100.0, "🟢"),  # High profit
    )

    def __init__(
        self,
        min_profit: float = -1.0,
        max_profit: float = 25.0,
    ) -> None:
        """
        Initialize PinnacleCalculator with configurable profit limits.

        Args:
            min_profit: Minimum acceptable profit % (default: -1.0, from .env)
            max_profit: Maximum acceptable profit % (default: 25.0, from .env)
        """
        super().__init__(min_profit=min_profit, max_profit=max_profit)

    @property
    def name(self) -> str:
        """Identifier for Pinnacle."""
        return "pinnaclesports"

    def calculate_stake(self, profit: float) -> Optional[StakeResult]:
        """
        Calculate stake indicator emoji based on surebet profit.

        Args:
            profit: Surebet profit percentage (e.g., 2.5 means 2.5%)

        Returns:
            StakeResult with emoji, or None if out of range

        Example:
            >>> calc = PinnacleCalculator()
            >>> result = calc.calculate_stake(2.5)
            >>> result.emoji
            '🟡'
        """
        # Check if profit is within acceptable range (uses injected limits)
        if not self.is_valid_profit(profit):
            return None

        # Find matching stake range
        for range_min, range_max, emoji in self.STAKE_RANGES:
            if range_min <= profit < range_max:
                return StakeResult(emoji=emoji)

        # Edge case: exactly at range_max of last range
        if profit >= self.STAKE_RANGES[-1][0]:
            emoji = self.STAKE_RANGES[-1][2]
            return StakeResult(emoji=emoji)

        return None

    def calculate_min_odds(self, sharp_odds: float) -> MinOddsResult:
        """
        Calculate minimum acceptable odds in soft bookmaker.

        ⚠️ USES CORRECT FORMULA from ADR-003:
            min_odds = 1 / (1.01 - 1/sharp_odds)

        ❌ DO NOT use legacy V6 formula (it was WRONG!)

        Args:
            sharp_odds: Odds of OPPOSITE market in Pinnacle (must be > 1.0)

        Returns:
            MinOddsResult with minimum odds

        Raises:
            ValueError: If sharp_odds <= 1.0

        Example:
            >>> calc = PinnacleCalculator()
            >>> result = calc.calculate_min_odds(2.05)
            >>> round(result.min_odds, 2)
            1.92
        """
        # Validate input to prevent mathematical errors
        if sharp_odds <= 1.0:
            raise ValueError(f"sharp_odds must be > 1.0, got {sharp_odds}")

        # CORRECT formula from ADR-003
        # min_odds = 1 / (1.01 - 1/sharp_odds)
        # Where 1.01 represents accepting up to -1% profit (1 + 0.01)
        implied_prob_sharp = 1 / sharp_odds
        min_odds = 1 / (1.01 - implied_prob_sharp)

        return MinOddsResult(
            min_odds=round(min_odds, 2),
            profit_threshold=self.PROFIT_THRESHOLD,
        )
