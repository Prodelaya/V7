"""Profit validator for pick validation."""

from typing import Tuple

from .base import BaseValidator


class ProfitValidator(BaseValidator):
    """
    Validates that profit is within acceptable range.
    
    Default range: -1% to 25%
    """
    
    def __init__(self, min_profit: float = -1.0, max_profit: float = 25.0):
        self._min_profit = min_profit
        self._max_profit = max_profit
    
    @property
    def name(self) -> str:
        return "profit_validator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, str | None]:
        """Validate profit is within range."""
        try:
            profit = float(pick_data.get("profit", 0))
            
            if not self._min_profit <= profit <= self._max_profit:
                return (
                    False,
                    f"Profit {profit}% outside range [{self._min_profit}%, {self._max_profit}%]"
                )
            
            return (True, None)
            
        except (ValueError, TypeError) as e:
            return (False, f"Invalid profit data: {e}")
