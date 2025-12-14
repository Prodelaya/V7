"""Profit validator - OPTIONAL SAFETY CHECK for profit range.

This validator is OPTIONAL since ADR-015 implements origin filtering:
- API parameter `min-profit=-1` already filters minimum profit
- API parameter `max-profit=25` already filters maximum profit

Keep as safety check in case:
- API parameters change or fail silently
- Configuration mismatch between API params and validator

Implementation Requirements:
- Validate profit between MIN_PROFIT (-1%) and MAX_PROFIT (25%)
- CPU-only operation (no I/O) - ~0ms overhead

Reference:
- docs/03-ADRs.md: ADR-015 (Origin Filtering)
- docs/05-Implementation.md: Task 3.3
- docs/01-SRS.md: RF-003 (validation requirements)

TODO: Implement ProfitValidator
"""

from typing import Tuple, Optional

from .base import BaseValidator


class ProfitValidator(BaseValidator):
    """
    OPTIONAL SAFETY CHECK: Validator for surebet profit range.
    
    Since ADR-015, the API filters profit at origin with min-profit/max-profit.
    This validator serves as a redundant safety check (~0ms overhead).
    
    Can be disabled in validation chain if full trust in API is desired.
    
    Checks that profit is within configured range:
    - Minimum: -1% (from SRS)
    - Maximum: 25% (from SRS)
    
    TODO: Implement based on:
    - ADR-015 in docs/03-ADRs.md
    - Task 3.3 in docs/05-Implementation.md
    - RF-003 in docs/01-SRS.md
    """
    
    def __init__(self, min_profit: float = -1.0, max_profit: float = 25.0):
        """
        Initialize with profit range.
        
        Args:
            min_profit: Minimum acceptable profit percent (default -1%)
            max_profit: Maximum acceptable profit percent (default 25%)
        """
        self._min_profit = min_profit
        self._max_profit = max_profit
    
    @property
    def name(self) -> str:
        return "ProfitValidator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if profit is within range.
        
        Args:
            pick_data: Must contain profit value
            
        Returns:
            (True, None) if valid
            (False, "message") if invalid
        """
        raise NotImplementedError("ProfitValidator.validate not implemented")
