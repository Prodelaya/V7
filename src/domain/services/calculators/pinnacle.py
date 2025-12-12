"""Pinnacle-specific odds calculator."""

from ...value_objects.odds import Odds
from ...value_objects.profit import Profit
from .base import BaseCalculator


class PinnacleCalculator(BaseCalculator):
    """
    Calculator for Pinnacle Sports.
    
    Pinnacle has approximately 2-3% margin on most markets.
    Formula: min_odds = 1 / (1 + target_profit/100 - 1/sharp_odds)
    """
    
    PINNACLE_MARGIN = 0.025  # 2.5% average margin
    
    @property
    def bookmaker_name(self) -> str:
        return "pinnaclesports"
    
    @property
    def margin(self) -> float:
        return self.PINNACLE_MARGIN
    
    def calculate_min_odds(
        self,
        sharp_odds: Odds,
        target_profit: float = -1.0
    ) -> Odds:
        """
        Calculate minimum acceptable odds for soft bookmaker.
        
        Uses formula: min_odds = 1 / (1 + target_profit/100 - 1/sharp_odds)
        For target_profit = -1%: min_odds = 1 / (1.01 - 1/sharp_odds)
        
        Args:
            sharp_odds: Pinnacle odds
            target_profit: Minimum acceptable profit (default -1%)
            
        Returns:
            Minimum odds needed in soft bookmaker
        """
        # Convert percentage to decimal (e.g., -1 -> -0.01)
        profit_decimal = target_profit / 100
        
        # Calculate denominator
        denominator = 1 + profit_decimal - (1 / sharp_odds.value)
        
        # Handle edge cases
        if denominator <= 0:
            return Odds(Odds.MAX_ODDS)
        
        min_odds_value = 1 / denominator
        
        # Clamp to valid range
        min_odds_value = max(Odds.MIN_ODDS, min(Odds.MAX_ODDS, min_odds_value))
        
        return Odds(round(min_odds_value, 2))
    
    def calculate_value(self, soft_odds: Odds, sharp_odds: Odds) -> Profit:
        """
        Calculate expected value/profit percentage.
        
        Formula: profit = (1/sharp_odds + 1/soft_odds - 1) * 100
        
        Args:
            soft_odds: Odds from soft bookmaker
            sharp_odds: Odds from Pinnacle
            
        Returns:
            Profit percentage as Profit value object
        """
        # Surebet profit formula
        combined_probability = (1 / sharp_odds.value) + (1 / soft_odds.value)
        profit_value = (combined_probability - 1) * 100
        
        return Profit(round(profit_value, 2))
