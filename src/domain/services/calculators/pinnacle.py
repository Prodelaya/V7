"""Pinnacle-specific calculator implementation.

Implementation Requirements:
- Implement BaseCalculator for Pinnacle Sports
- Use CORRECT min_odds formula: 1 / (1.01 - 1/sharp_odds)
- Stake ranges from docs/01-SRS.md RF-005

Reference:
- docs/02-PDR.md: Section 4.1 (Strategy Pattern)
- docs/05-Implementation.md: Task 2.2
- docs/03-ADRs.md: ADR-003 (CORRECT formula)
- docs/01-SRS.md: RF-005, RF-006, Appendix 6.2

⚠️ CRITICAL: The legacy V6 formula was WRONG! See ADR-003.

TODO: Implement PinnacleCalculator
"""

from typing import Optional

from .base import BaseCalculator, StakeResult, MinOddsResult


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
    
    TODO: Implement based on:
    - Task 2.2 in docs/05-Implementation.md
    - ADR-003 in docs/03-ADRs.md
    - get_stake() in legacy/RetadorV6.py (line 1267) - Pinnacle branch ONLY
    """
    
    # Profit ranges: (min_profit, max_profit, emoji, confidence, units)
    # Reference: docs/01-SRS.md RF-005
    PROFIT_RANGES = [
        (-1.0, -0.5, "🔴", 0.25, (0.5, 1.0, 1.5)),
        (-0.5,  1.5, "🟠", 0.50, (1.0, 1.5, 2.0)),
        ( 1.5,  4.0, "🟡", 0.75, (1.5, 2.0, 3.0)),
        ( 4.0, 25.0, "🟢", 1.00, (2.0, 3.0, 4.0)),
    ]
    
    # Profit limits
    MIN_PROFIT = -1.0   # Minimum acceptable (%)
    MAX_PROFIT = 25.0   # Maximum acceptable (%)
    
    # Profit threshold for min_odds calculation (as decimal)
    PROFIT_THRESHOLD = -0.01  # -1%
    
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
            StakeResult with emoji and units, or None if out of range
        
        Example:
            >>> calc = PinnacleCalculator()
            >>> result = calc.calculate_stake(2.5)
            >>> result.emoji
            '🟡'
        """
        raise NotImplementedError("PinnacleCalculator.calculate_stake not implemented")
    
    def calculate_min_odds(self, sharp_odds: float) -> MinOddsResult:
        """
        Calculate minimum acceptable odds in soft bookmaker.
        
        ⚠️ USE CORRECT FORMULA from ADR-003:
            min_odds = 1 / (1.01 - 1/sharp_odds)
        
        ❌ DO NOT use legacy V6 formula (it was WRONG!)
        
        Args:
            sharp_odds: Odds of OPPOSITE market in Pinnacle
            
        Returns:
            MinOddsResult with minimum odds
        
        Example:
            >>> calc = PinnacleCalculator()
            >>> result = calc.calculate_min_odds(2.05)
            >>> result.min_odds
            1.92
        """
        raise NotImplementedError("PinnacleCalculator.calculate_min_odds not implemented")
    
    def is_valid_profit(self, profit: float) -> bool:
        """
        Check if profit is within acceptable range.
        
        Args:
            profit: Surebet profit percentage
            
        Returns:
            True if -1% <= profit <= 25%
        """
        raise NotImplementedError("PinnacleCalculator.is_valid_profit not implemented")