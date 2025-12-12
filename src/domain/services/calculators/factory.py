"""Calculator factory for getting sharp-specific calculators.

Implementation Requirements:
- Get calculator by bookmaker name (case-insensitive)
- Default to PinnacleCalculator for unknown sharps
- Cache calculator instances

Reference:
- docs/02-PDR.md: Section 4.1 (Strategy Pattern)
- docs/05-Implementation.md: Task 2.3

TODO: Implement CalculatorFactory
"""

from typing import Dict, Optional

from .base import BaseCalculator
from .pinnacle import PinnacleCalculator


class CalculatorFactory:
    """
    Factory for getting sharp-specific calculators.
    
    Implements Factory Pattern to provide the correct calculator
    based on the sharp bookmaker name.
    
    TODO: Implement based on:
    - Task 2.3 in docs/05-Implementation.md
    """
    
    def __init__(self):
        """Initialize factory with available calculators."""
        self._calculators: Dict[str, BaseCalculator] = {}
        self._default: Optional[BaseCalculator] = None
    
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
        """
        raise NotImplementedError("CalculatorFactory.get_calculator not implemented")
    
    def register(self, bookmaker: str, calculator: BaseCalculator) -> None:
        """
        Register a calculator for a bookmaker.
        
        Args:
            bookmaker: Bookmaker name
            calculator: Calculator instance
        """
        raise NotImplementedError("CalculatorFactory.register not implemented")