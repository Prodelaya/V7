"""Calculation service for stake and min odds.

Implementation Requirements:
- Orchestrate calculators based on sharp bookmaker
- Use CalculatorFactory to get correct strategy
- Expose calculate_stake() and calculate_min_odds()

Reference:
- docs/04-Structure.md: "domain/services/"
- docs/05-Implementation.md: Task 2.4
- docs/02-PDR.md: Section 3.1.3 (Domain Services)

TODO: Implement CalculationService
"""

from typing import Optional

from .calculators.factory import CalculatorFactory
from .calculators.base import StakeResult, MinOddsResult


class CalculationService:
    """
    Domain service for pick calculations.
    
    Orchestrates the calculator strategy pattern to compute:
    - Stake recommendation (emoji + confidence)
    - Minimum acceptable odds in soft bookmaker
    
    TODO: Implement based on:
    - Task 2.4 in docs/05-Implementation.md
    - Section 3.1.3 in docs/02-PDR.md
    """
    
    def __init__(self, calculator_factory: Optional[CalculatorFactory] = None):
        """
        Initialize CalculationService.
        
        Args:
            calculator_factory: Factory for getting calculators by bookmaker
        """
        self._factory = calculator_factory or CalculatorFactory()
    
    def calculate_stake(
        self, 
        profit: float, 
        sharp_bookmaker: str
    ) -> Optional[StakeResult]:
        """
        Calculate recommended stake based on profit and sharp bookmaker.
        
        Args:
            profit: Surebet profit percentage
            sharp_bookmaker: Name of the sharp bookmaker
            
        Returns:
            StakeResult with emoji and confidence, or None if rejected
        
        Reference: RF-005 in docs/01-SRS.md
        """
        raise NotImplementedError("CalculationService.calculate_stake not implemented")
    
    def calculate_min_odds(
        self, 
        sharp_odds: float, 
        sharp_bookmaker: str
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
        raise NotImplementedError("CalculationService.calculate_min_odds not implemented")
