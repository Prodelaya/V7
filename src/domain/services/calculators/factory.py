"""Factory for creating calculator instances."""

from typing import Dict, Optional, Type, List

from .base import BaseCalculator
from .pinnacle import PinnacleCalculator


class CalculatorFactory:
    """
    Factory for creating and caching calculator instances.
    
    Uses Singleton pattern per calculator type to avoid
    creating multiple instances of the same calculator.
    
    Usage:
        >>> calculator = CalculatorFactory.get("pinnaclesports")
        >>> stake = calculator.calculate_stake(profit=2.5)
        
    To add a new sharp bookmaker:
        1. Create new calculator class extending BaseCalculator
        2. Register it: CalculatorFactory.register("betfair", BetfairCalculator)
    """
    
    # Registry of calculator classes by bookmaker name
    _registry: Dict[str, Type[BaseCalculator]] = {
        "pinnaclesports": PinnacleCalculator,
        "pinnacle": PinnacleCalculator,  # Alias
    }
    
    # Cache of instantiated calculators (singleton per type)
    _instances: Dict[str, BaseCalculator] = {}
    
    @classmethod
    def get(cls, bookmaker: str) -> Optional[BaseCalculator]:
        """
        Get calculator instance for a sharp bookmaker.
        
        Args:
            bookmaker: Name of the sharp bookmaker (e.g., "pinnaclesports")
            
        Returns:
            Calculator instance, or None if bookmaker not registered
            
        Examples:
            >>> calc = CalculatorFactory.get("pinnaclesports")
            >>> calc.name
            'pinnaclesports'
            
            >>> CalculatorFactory.get("unknown_bookie")
            None
        """
        normalized = bookmaker.lower().strip()
        
        # Return cached instance if exists
        if normalized in cls._instances:
            return cls._instances[normalized]
        
        # Look up calculator class in registry
        calculator_class = cls._registry.get(normalized)
        
        if calculator_class is None:
            return None  # Explicit: bookmaker not supported
        
        # Create, cache, and return new instance
        instance = calculator_class()
        cls._instances[normalized] = instance
        
        return instance
    
    @classmethod
    def get_or_raise(cls, bookmaker: str) -> BaseCalculator:
        """
        Get calculator instance, raising exception if not found.
        
        Args:
            bookmaker: Name of the sharp bookmaker
            
        Returns:
            Calculator instance
            
        Raises:
            ValueError: If bookmaker is not registered
        """
        calculator = cls.get(bookmaker)
        
        if calculator is None:
            available = cls.available_bookmakers()
            raise ValueError(
                f"No calculator registered for '{bookmaker}'. "
                f"Available: {available}"
            )
        
        return calculator
    
    @classmethod
    def register(cls, bookmaker: str, calculator_class: Type[BaseCalculator]) -> None:
        """
        Register a new calculator for a bookmaker.
        
        Args:
            bookmaker: Name identifier for the bookmaker
            calculator_class: Class implementing BaseCalculator
            
        Examples:
            >>> CalculatorFactory.register("betfair", BetfairCalculator)
        """
        normalized = bookmaker.lower().strip()
        cls._registry[normalized] = calculator_class
        
        # Clear cached instance if exists (in case of re-registration)
        if normalized in cls._instances:
            del cls._instances[normalized]
    
    @classmethod
    def available_bookmakers(cls) -> List[str]:
        """
        Get list of registered bookmaker names.
        
        Returns:
            List of bookmaker identifiers that have calculators
        """
        # Return unique names (remove aliases)
        unique = set()
        for name, calc_class in cls._registry.items():
            # Use the actual calculator name, not alias
            unique.add(name)
        return sorted(unique)
    
    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached calculator instances.
        
        Useful for testing or when re-registering calculators.
        """
        cls._instances.clear()