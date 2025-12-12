"""Odds validator for pick validation."""

from typing import Tuple

from .base import BaseValidator


class OddsValidator(BaseValidator):
    """
    Validates that odds are within acceptable range.
    
    Default range: 1.10 to 9.99
    """
    
    def __init__(self, min_odds: float = 1.10, max_odds: float = 9.99):
        self._min_odds = min_odds
        self._max_odds = max_odds
    
    @property
    def name(self) -> str:
        return "odds_validator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, str | None]:
        """Validate odds are within range."""
        try:
            # Get odds from soft prong
            prongs = pick_data.get("prongs", [])
            
            for prong in prongs:
                odds = float(prong.get("odd", 0))
                
                if not self._min_odds <= odds <= self._max_odds:
                    return (
                        False,
                        f"Odds {odds} outside range [{self._min_odds}, {self._max_odds}]"
                    )
            
            return (True, None)
            
        except (ValueError, TypeError, KeyError) as e:
            return (False, f"Invalid odds data: {e}")
