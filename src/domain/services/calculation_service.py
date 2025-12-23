"""Calculation service for stake and min odds.

Orchestrates calculators based on sharp bookmaker using the Strategy Pattern.
Uses CalculatorFactory to get the correct calculator implementation.

Reference:
- docs/04-Structure.md: "domain/services/"
- docs/05-Implementation.md: Task 2.4
- docs/02-PDR.md: Section 3.1.3 (Domain Services)
"""

from typing import Optional

from .calculators.base import MinOddsResult, StakeResult
from .calculators.factory import CalculatorFactory


class CalculationService:
    """
    Domain service for pick calculations.

    Orchestrates the calculator strategy pattern to compute:
    - Stake recommendation (emoji indicator)
    - Minimum acceptable odds in soft bookmaker

    Example:
        >>> service = CalculationService()
        >>> stake = service.calculate_stake(2.5, "pinnaclesports")
        >>> stake.emoji
        '🟡'
        >>> min_odds = service.calculate_min_odds(2.05, "pinnaclesports")
        >>> min_odds.min_odds
        1.91
    """

    def __init__(self, calculator_factory: Optional[CalculatorFactory] = None):
        """
        Initialize CalculationService.

        Args:
            calculator_factory: Factory for getting calculators by bookmaker.
                               If None, creates default factory.
        """
        self._factory = calculator_factory or CalculatorFactory()

    def calculate_stake(
        self,
        profit: float,
        sharp_bookmaker: str,
    ) -> Optional[StakeResult]:
        """
        Calculate stake indicator based on profit and sharp bookmaker.

        Args:
            profit: Surebet profit percentage
            sharp_bookmaker: Name of the sharp bookmaker

        Returns:
            StakeResult with emoji, or None if rejected

        Reference: RF-005 in docs/01-SRS.md
        """
        calculator = self._factory.get_calculator(sharp_bookmaker)
        return calculator.calculate_stake(profit)

    def calculate_min_odds(
        self,
        sharp_odds: float,
        sharp_bookmaker: str,
    ) -> MinOddsResult:
        """
        Calculate minimum acceptable odds for soft bookmaker.

        Args:
            sharp_odds: Odds of opposite market in sharp bookmaker
            sharp_bookmaker: Name of the sharp bookmaker

        Returns:
            MinOddsResult with minimum odds value

        Reference: RF-006 in docs/01-SRS.md
        """
        calculator = self._factory.get_calculator(sharp_bookmaker)
        return calculator.calculate_min_odds(sharp_odds)
