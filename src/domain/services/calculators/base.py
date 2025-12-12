"""Base calculator interface and result dataclasses.

Implementation Requirements:
- Abstract base class with calculate_stake() and calculate_min_odds()
- StakeResult dataclass with emoji, confidence, units_suggestion
- MinOddsResult dataclass with min_odds, profit_threshold

Reference:
- docs/02-PDR.md: Section 4.1 (Strategy Pattern)
- docs/05-Implementation.md: Task 2.1
- docs/03-ADRs.md: ADR-002

TODO: Implement BaseCalculator interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class StakeResult:
    """
    Result of stake calculation.
    
    Attributes:
        emoji: Stake indicator emoji (🔴, 🟠, 🟡, 🟢)
        confidence: Confidence level (0.0 - 1.0)
        units_suggestion: Tuple of (min, recommended, max) units
    
    Reference: RF-005 in docs/01-SRS.md
    """
    emoji: str
    confidence: float
    units_suggestion: Tuple[float, float, float]


@dataclass(frozen=True)
class MinOddsResult:
    """
    Result of minimum odds calculation.
    
    Attributes:
        min_odds: Minimum acceptable odds in soft bookmaker
        profit_threshold: Profit threshold used (e.g., -0.01 for -1%)
    
    Reference: RF-006 in docs/01-SRS.md
    """
    min_odds: float
    profit_threshold: float


class BaseCalculator(ABC):
    """
    Abstract base class for sharp-specific calculators.
    
    Implements Strategy Pattern - each sharp bookmaker has its own
    calculator with specific formulas and ranges.
    
    TODO: Implement based on:
    - Task 2.1 in docs/05-Implementation.md
    - ADR-002 in docs/03-ADRs.md
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Identifier for this calculator's sharp bookmaker.
        
        Returns:
            Bookmaker name (e.g., "pinnaclesports")
        """
        pass
    
    @abstractmethod
    def calculate_stake(self, profit: float) -> Optional[StakeResult]:
        """
        Calculate recommended stake based on surebet profit.
        
        Args:
            profit: Surebet profit percentage (e.g., 2.5 means 2.5%)
            
        Returns:
            StakeResult with emoji and units, or None if profit out of range
        
        Reference: RF-005 in docs/01-SRS.md
        
        Ranges for Pinnacle (from SRS):
            | Profit       | Emoji | Confidence |
            |--------------|-------|------------|
            | -1% to -0.5% | 🔴    | Low        |
            | -0.5% to 1.5%| 🟠    | Medium-low |
            | 1.5% to 4%   | 🟡    | Medium-high|
            | >4%          | 🟢    | High       |
        """
        pass
    
    @abstractmethod
    def calculate_min_odds(self, sharp_odds: float) -> MinOddsResult:
        """
        Calculate minimum acceptable odds in soft bookmaker.
        
        This is the lowest odds at which we still have acceptable value
        (typically -1% profit threshold).
        
        Args:
            sharp_odds: Odds of OPPOSITE market in sharp bookmaker
            
        Returns:
            MinOddsResult with minimum odds value
        
        Reference: 
            - RF-006 in docs/01-SRS.md
            - ADR-003 in docs/03-ADRs.md (CORRECT formula)
        
        ⚠️ CORRECT Formula (from ADR-003):
            min_odds = 1 / (1.01 - 1/sharp_odds)
        
        ❌ WRONG Formula (from legacy V6 - DO NOT USE):
            oddmin = 1 / (margin - prob_contraria - (1/100))
        """
        pass
    
    @abstractmethod
    def is_valid_profit(self, profit: float) -> bool:
        """
        Check if profit is within acceptable range for this sharp.
        
        Args:
            profit: Surebet profit percentage
            
        Returns:
            True if profit is acceptable
        """
        pass
