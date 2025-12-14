"""Odds validator - OPTIONAL SAFETY CHECK for odds range.

This validator is OPTIONAL since ADR-015 implements origin filtering:
- API parameter `min-odds=1.10` already filters minimum odds
- API parameter `max-odds=9.99` already filters maximum odds

Keep as safety check in case:
- API parameters change or fail silently
- Configuration mismatch between API params and validator

Implementation Requirements:
- Validate odds between MIN_ODDS (1.10) and MAX_ODDS (9.99)
- CPU-only operation (no I/O) - ~0ms overhead

Reference:
- docs/03-ADRs.md: ADR-015 (Origin Filtering)
- docs/05-Implementation.md: Task 3.2
- docs/01-SRS.md: RF-003 (validation requirements)

TODO: Implement OddsValidator
"""

from typing import Tuple, Optional

from .base import BaseValidator


class OddsValidator(BaseValidator):
    """
    OPTIONAL SAFETY CHECK: Validator for betting odds range.
    
    Since ADR-015, the API filters odds at origin with min-odds/max-odds.
    This validator serves as a redundant safety check (~0ms overhead).
    
    Can be disabled in validation chain if full trust in API is desired.
    
    Checks that odds are within configured range:
    - Minimum: 1.10 (from SRS)
    - Maximum: 9.99 (from SRS)
    
    TODO: Implement based on:
    - ADR-015 in docs/03-ADRs.md
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
