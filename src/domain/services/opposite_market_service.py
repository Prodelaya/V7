"""Service for handling opposite market lookups."""

from typing import List

from ..value_objects.market_type import MarketType, OPPOSITE_MARKETS


class OppositeMarketService:
    """
    Service for determining opposite markets.
    
    Used to prevent sending both sides of a surebet (rebotes).
    """
    
    def get_opposites(self, market_type: MarketType) -> List[MarketType]:
        """
        Get all opposite market types for a given market.
        
        Args:
            market_type: The market type to find opposites for
            
        Returns:
            List of opposite MarketType objects
        """
        opposite_values = market_type.opposites
        return [MarketType(value) for value in opposite_values]
    
    def are_opposites(self, market1: MarketType, market2: MarketType) -> bool:
        """
        Check if two market types are opposites.
        
        Args:
            market1: First market type
            market2: Second market type
            
        Returns:
            True if markets are opposites
        """
        return market1.is_opposite_of(market2)
    
    def generate_opposite_keys(
        self,
        base_key: str,
        market_type: MarketType,
        bookmaker: str
    ) -> List[str]:
        """
        Generate Redis keys for all opposite markets.
        
        Args:
            base_key: Base key (teams:timestamp)
            market_type: Current market type
            bookmaker: Target bookmaker
            
        Returns:
            List of Redis keys for opposite markets
        """
        keys = []
        for opposite in self.get_opposites(market_type):
            keys.append(f"{base_key}:{opposite.value}:{bookmaker}")
        return keys
