"""Odds validator - Check if odds are within acceptable range.

Implementation Requirements:
- Validate odds between MIN_ODDS (1.10) and MAX_ODDS (9.99)
- CPU-only operation (no I/O)

Reference:
- docs/05-Implementation.md: Task 3.2
- docs/01-SRS.md: RF-003 (validation requirements)

TODO: Implement OddsValidator
"""

from typing import Tuple, Optional

from .base import BaseValidator


class OddsValidator(BaseValidator):
    """
    Validator for betting odds range.
    
    Checks that odds are within configured range:
    - Minimum: 1.10 (from SRS)
    - Maximum: 9.99 (from SRS)
    
    TODO: Implement based on:
    - Task 3.2 in docs/05-Implementation.md
    - RF-003 in docs/01-SRS.md
    """
    
    def __init__(self, min_odds: float = 1.10, max_odds: float = 9.99):
        """
        Initialize with odds range.
        
        Args:
            min_odds: Minimum acceptable odds (default 1.10)
            max_odds: Maximum acceptable odds (default 9.99)
        """
        self._min_odds = min_odds
        self._max_odds = max_odds
    
    @property
    def name(self) -> str:
        return "OddsValidator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if odds are within range.
        
        Args:
            pick_data: Must contain odds value
            
        Returns:
            (True, None) if valid
            (False, "message") if invalid
        """
        raise NotImplementedError("OddsValidator.validate not implemented")
