"""Base calculator interface for sharp bookmaker strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class StakeResult:
    """Result of stake calculation."""
    emoji: str                              # 🔴🟠🟡🟢
    confidence: float                       # 0.0 a 1.0
    units_suggestion: Tuple[float, float, float]  # (conservador, normal, agresivo)


@dataclass(frozen=True)
class MinOddsResult:
    """Result of minimum odds calculation."""
    min_odds: float
    profit_threshold: float  # El profit mínimo usado (ej: -0.01)


class BaseCalculator(ABC):
    """
    Abstract base class for sharp bookmaker calculators.
    
    Each sharp bookmaker (Pinnacle, Bet365, etc.) can have different
    rules for calculating stake recommendations and minimum acceptable odds.
    
    Strategy Pattern: Allows adding new sharps without modifying existing code.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Identifier name of the sharp bookmaker.
        
        Examples: 'pinnaclesports', 'bet365'
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
        """
        pass
    
    @abstractmethod
    def calculate_min_odds(self, sharp_odds: float) -> MinOddsResult:
        """
        Calculate minimum acceptable odds in soft bookmaker.
        
        Formula: min_odds = 1 / (1 - profit_threshold - 1/sharp_odds)
        
        Args:
            sharp_odds: Odds of the OPPOSITE market in the sharp bookmaker
            
        Returns:
            MinOddsResult with calculated minimum odds
        """
        pass
    
    @abstractmethod
    def is_valid_profit(self, profit: float) -> bool:
        """
        Check if profit is within acceptable range for this sharp.
        
        Args:
            profit: Surebet profit percentage
            
        Returns:
            True if profit is acceptable, False otherwise
        """
        pass
