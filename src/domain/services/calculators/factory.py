"""Factory for creating calculator instances."""

from typing import Dict, Type

from .base import BaseCalculator
from .pinnacle import PinnacleCalculator


class CalculatorFactory:
    """
    Factory for creating calculator instances based on bookmaker.
    
    Allows for different calculation strategies per sharp bookmaker.
    """
    
    _calculators: Dict[str, Type[BaseCalculator]] = {
        "pinnaclesports": PinnacleCalculator,
        "pinnacle": PinnacleCalculator,
    }
    
    _instances: Dict[str, BaseCalculator] = {}
    
    def get_calculator(self, bookmaker: str) -> BaseCalculator:
        """
        Get calculator instance for a bookmaker.
        
        Args:
            bookmaker: Name of the sharp bookmaker
            
        Returns:
            Calculator instance for the bookmaker
            
        Raises:
            ValueError: If no calculator exists for the bookmaker
        """
        bookmaker_lower = bookmaker.lower()
        
        # Return cached instance if available
        if bookmaker_lower in self._instances:
            return self._instances[bookmaker_lower]
        
        # Create new instance
        calculator_class = self._calculators.get(bookmaker_lower)
        if calculator_class is None:
            # Default to Pinnacle calculator
            calculator_class = PinnacleCalculator
        
        instance = calculator_class()
        self._instances[bookmaker_lower] = instance
        return instance
    
    @classmethod
    def register_calculator(
        cls, 
        bookmaker: str, 
        calculator_class: Type[BaseCalculator]
    ) -> None:
        """Register a new calculator for a bookmaker."""
        cls._calculators[bookmaker.lower()] = calculator_class
