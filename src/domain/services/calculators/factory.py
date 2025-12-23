"""Calculator factory for getting sharp-specific calculators.

Implements Factory Pattern with Dependency Injection for profit limits.
The factory receives limits from Settings/.env and passes them to calculators.

Reference:
- docs/02-PDR.md: Section 4.1 (Strategy Pattern)
- docs/05-Implementation.md: Task 2.3
"""

from typing import Dict, Optional

from .base import DEFAULT_MAX_PROFIT, DEFAULT_MIN_PROFIT, BaseCalculator
from .pinnacle import PinnacleCalculator


class CalculatorFactory:
    """
    Factory for getting sharp-specific calculators.

    Implements Factory Pattern with Dependency Injection - the factory
    receives profit limits from Settings/.env and passes them to all
    calculators it creates.

    Example:
        >>> # In application layer, create factory with limits from Settings
        >>> settings = Settings.from_env()
        >>> factory = CalculatorFactory(
        ...     min_profit=settings.validation.min_profit,
        ...     max_profit=settings.validation.max_profit
        ... )
        >>> calc = factory.get_calculator("pinnaclesports")
        >>> calc.min_profit
        -1.0
    """

    def __init__(
        self,
        min_profit: float = DEFAULT_MIN_PROFIT,
        max_profit: float = DEFAULT_MAX_PROFIT,
    ) -> None:
        """
        Initialize factory with configurable profit limits.

        Args:
            min_profit: Minimum acceptable profit % (default: -1.0, from .env)
            max_profit: Maximum acceptable profit % (default: 25.0, from .env)
        """
        self._min_profit = min_profit
        self._max_profit = max_profit
        self._calculators: Dict[str, BaseCalculator] = {}
        self._default: Optional[BaseCalculator] = None

        # Pre-register known calculators
        self._register_default_calculators()

    def _register_default_calculators(self) -> None:
        """Register default calculators with injected limits."""
        # Pinnacle is the default and most common sharp
        pinnacle = PinnacleCalculator(
            min_profit=self._min_profit,
            max_profit=self._max_profit,
        )
        self.register("pinnaclesports", pinnacle)
        self._default = pinnacle

    def get_calculator(self, bookmaker: str) -> BaseCalculator:
        """
        Get calculator for a specific bookmaker.

        Args:
            bookmaker: Bookmaker name (case-insensitive)

        Returns:
            Calculator for that bookmaker, or default if not found

        Example:
            >>> factory = CalculatorFactory()
            >>> calc = factory.get_calculator("pinnaclesports")
            >>> isinstance(calc, PinnacleCalculator)
            True
            >>> calc = factory.get_calculator("PINNACLESPORTS")  # Case insensitive
            >>> isinstance(calc, PinnacleCalculator)
            True
        """
        key = bookmaker.lower().strip()

        # Look for exact match
        if key in self._calculators:
            return self._calculators[key]

        # Look for partial match (e.g., "pinnacle" matches "pinnaclesports")
        for registered_key, calculator in self._calculators.items():
            if key in registered_key or registered_key in key:
                return calculator

        # Return default calculator (Pinnacle)
        if self._default is not None:
            return self._default

        # Fallback: create new Pinnacle calculator
        return PinnacleCalculator(
            min_profit=self._min_profit,
            max_profit=self._max_profit,
        )

    def register(self, bookmaker: str, calculator: BaseCalculator) -> None:
        """
        Register a calculator for a bookmaker.

        Args:
            bookmaker: Bookmaker name (will be normalized to lowercase)
            calculator: Calculator instance
        """
        key = bookmaker.lower().strip()
        self._calculators[key] = calculator
