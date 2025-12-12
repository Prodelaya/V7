"""Base calculator interface."""

from abc import ABC, abstractmethod

from ...value_objects.odds import Odds
from ...value_objects.profit import Profit


class BaseCalculator(ABC):
    """
    Abstract base class for odds calculators.
    
    Each sharp bookmaker may have different margin calculations,
    requiring specific calculator implementations.
    """
    
    @property
    @abstractmethod
    def bookmaker_name(self) -> str:
        """Name of the sharp bookmaker."""
        pass
    
    @property
    @abstractmethod
    def margin(self) -> float:
        """Estimated margin for this bookmaker."""
        pass
    
    @abstractmethod
    def calculate_min_odds(
        self,
        sharp_odds: Odds,
        target_profit: float = -1.0
    ) -> Odds:
        """
        Calculate minimum acceptable odds for a soft bookmaker.
        
        Args:
            sharp_odds: Odds from the sharp bookmaker
            target_profit: Minimum acceptable profit percentage
            
        Returns:
            Minimum odds needed to maintain target profit
        """
        pass
    
    @abstractmethod
    def calculate_value(self, soft_odds: Odds, sharp_odds: Odds) -> Profit:
        """
        Calculate the expected value/profit of a bet.
        
        Args:
            soft_odds: Odds from the soft bookmaker
            sharp_odds: Odds from the sharp bookmaker
            
        Returns:
            Profit value object with calculated profit percentage
        """
        pass
