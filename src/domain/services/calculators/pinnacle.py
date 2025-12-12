"""Pinnacle-specific calculator implementation."""

from typing import Optional

from .base import BaseCalculator, StakeResult, MinOddsResult


class PinnacleCalculator(BaseCalculator):
    """
    Calculator strategy for Pinnacle Sports as sharp bookmaker.
    
    Pinnacle is considered the market reference due to:
    - Low margins (~2-3%)
    - Winners accepted policy
    - Efficient odds that reflect true probabilities
    
    Stake ranges are based on surebet profit percentage:
    - 🔴 Low confidence: -1% to -0.5% profit
    - 🟠 Medium-low: -0.5% to 1.5% profit  
    - 🟡 Medium-high: 1.5% to 4% profit
    - 🟢 High confidence: >4% profit
    """
    
    # Profit ranges for stake calculation
    # (min_profit, max_profit, emoji, confidence, units)
    PROFIT_RANGES = [
        (-1.0, -0.5, "🔴", 0.25, (0.5, 1.0, 1.5)),
        (-0.5,  1.5, "🟠", 0.50, (1.0, 1.5, 2.0)),
        ( 1.5,  4.0, "🟡", 0.75, (1.5, 2.0, 3.0)),
        ( 4.0, 25.0, "🟢", 1.00, (2.0, 3.0, 4.0)),
    ]
    
    # Profit limits
    MIN_PROFIT = -1.0   # Minimum acceptable profit (%)
    MAX_PROFIT = 25.0   # Maximum acceptable profit (%)
    
    # Profit threshold for min_odds calculation
    PROFIT_THRESHOLD = -0.01  # -1% as decimal
    
    @property
    def name(self) -> str:
        """Identifier for Pinnacle."""
        return "pinnaclesports"
    
    def calculate_stake(self, profit: float) -> Optional[StakeResult]:
        """
        Calculate recommended stake based on surebet profit.
        
        Args:
            profit: Surebet profit percentage (e.g., 2.5 means 2.5%)
            
        Returns:
            StakeResult with emoji and unit suggestions, or None if invalid
            
        Examples:
            >>> calc = PinnacleCalculator()
            >>> result = calc.calculate_stake(2.5)
            >>> result.emoji
            '🟡'
            >>> result.units_suggestion
            (1.5, 2.0, 3.0)
        """
        if not self.is_valid_profit(profit):
            return None
        
        for min_p, max_p, emoji, confidence, units in self.PROFIT_RANGES:
            if min_p <= profit <= max_p:
                return StakeResult(
                    emoji=emoji,
                    confidence=confidence,
                    units_suggestion=units
                )
        
        return None  # Should not reach here if ranges are complete
    
    def calculate_min_odds(self, sharp_odds: float) -> MinOddsResult:
        """
        Calculate minimum acceptable odds in soft bookmaker to maintain -1% value.
        
        Formula derivation:
            profit = 1 - (1/odd_sharp + 1/odd_soft)
            For profit = -0.01 (-1%):
            -0.01 = 1 - (1/odd_sharp + 1/odd_soft)
            1/odd_soft = 1.01 - 1/odd_sharp
            odd_soft = 1 / (1.01 - 1/odd_sharp)
        
        Args:
            sharp_odds: Odds of the OPPOSITE market in Pinnacle
            
        Returns:
            MinOddsResult with minimum acceptable odds
            
        Examples:
            >>> calc = PinnacleCalculator()
            >>> result = calc.calculate_min_odds(2.05)
            >>> result.min_odds
            1.92
        """
        try:
            # Formula: min_odds = 1 / (1 - profit_threshold - 1/sharp_odds)
            # With profit_threshold = -0.01:
            # min_odds = 1 / (1 - (-0.01) - 1/sharp_odds)
            # min_odds = 1 / (1.01 - 1/sharp_odds)
            
            denominator = (1 - self.PROFIT_THRESHOLD) - (1 / sharp_odds)
            
            if denominator <= 0:
                # Sharp odds too low, would need impossible soft odds
                return MinOddsResult(
                    min_odds=99.99,
                    profit_threshold=self.PROFIT_THRESHOLD
                )
            
            min_odds = 1 / denominator
            
            return MinOddsResult(
                min_odds=round(min_odds, 2),
                profit_threshold=self.PROFIT_THRESHOLD
            )
            
        except (ZeroDivisionError, ValueError):
            return MinOddsResult(
                min_odds=99.99,
                profit_threshold=self.PROFIT_THRESHOLD
            )
    
    def is_valid_profit(self, profit: float) -> bool:
        """
        Check if profit is within acceptable range.
        
        Args:
            profit: Surebet profit percentage
            
        Returns:
            True if -1% <= profit <= 25%
        """
        return self.MIN_PROFIT <= profit <= self.MAX_PROFIT