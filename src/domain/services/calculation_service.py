"""Calculation service for odds and stakes."""

from typing import Protocol

from ..value_objects.odds import Odds
from ..value_objects.profit import Profit
from .calculators.factory import CalculatorFactory


class CalculationService:
    """
    Service for performing value bet calculations.
    
    Handles minimum odds calculation and stake recommendations
    based on sharp bookmaker odds.
    """
    
    def __init__(self):
        self._calculator_factory = CalculatorFactory()
    
    def calculate_min_odds(
        self,
        sharp_odds: Odds,
        sharp_bookmaker: str,
        target_profit: float = -1.0
    ) -> Odds:
        """
        Calculate minimum acceptable odds for a soft bookmaker.
        
        Args:
            sharp_odds: Odds from the sharp bookmaker
            sharp_bookmaker: Name of the sharp bookmaker
            target_profit: Minimum acceptable profit percentage
            
        Returns:
            Minimum odds needed to maintain target profit
        """
        calculator = self._calculator_factory.get_calculator(sharp_bookmaker)
        return calculator.calculate_min_odds(sharp_odds, target_profit)
    
    def calculate_value(
        self,
        soft_odds: Odds,
        sharp_odds: Odds,
        sharp_bookmaker: str
    ) -> Profit:
        """
        Calculate the expected value/profit of a bet.
        
        Args:
            soft_odds: Odds from the soft bookmaker
            sharp_odds: Odds from the sharp bookmaker
            sharp_bookmaker: Name of the sharp bookmaker
            
        Returns:
            Profit value object with calculated profit percentage
        """
        calculator = self._calculator_factory.get_calculator(sharp_bookmaker)
        return calculator.calculate_value(soft_odds, sharp_odds)
