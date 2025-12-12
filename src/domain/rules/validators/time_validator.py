"""Time validator - Check if event is in the future.

Implementation Requirements:
- Validate event time is in the future (>0 seconds from now)
- Handle timestamp format from API
- CPU-only operation (no I/O)

Reference:
- docs/05-Implementation.md: Task 3.4
- docs/01-SRS.md: RF-003 (validation requirements)

TODO: Implement TimeValidator
"""

from typing import Tuple, Optional

from .base import BaseValidator


class TimeValidator(BaseValidator):
    """
    Validator for event timing.
    
    Checks that event starts in the future (not already started).
    
    TODO: Implement based on:
    - Task 3.4 in docs/05-Implementation.md
    - RF-003 in docs/01-SRS.md
    - _get_spain_time() in legacy/RetadorV6.py (line 976)
    """
    
    def __init__(self, min_seconds: int = 0):
        """
        Initialize with minimum time buffer.
        
        Args:
            min_seconds: Minimum seconds until event (default 0)
        """
        self._min_seconds = min_seconds
    
    @property
    def name(self) -> str:
        return "TimeValidator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if event is in the future.
        
        Args:
            pick_data: Must contain 'time' field (timestamp)
            
        Returns:
            (True, None) if event is in future
            (False, "message") if event already started
        
        Note: API timestamp format has 3 extra digits (milliseconds)
        """
        raise NotImplementedError("TimeValidator.validate not implemented")
