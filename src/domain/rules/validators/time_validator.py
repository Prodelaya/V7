"""Time validator for pick validation."""

from typing import Tuple
from datetime import datetime

from .base import BaseValidator


class TimeValidator(BaseValidator):
    """
    Validates that event time is in the future.
    
    Events must be at least min_seconds in the future.
    """
    
    def __init__(self, min_seconds: int = 0):
        self._min_seconds = min_seconds
    
    @property
    def name(self) -> str:
        return "time_validator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, str | None]:
        """Validate event is in the future."""
        try:
            # API returns timestamp in milliseconds
            event_time_ms = int(pick_data.get("time", 0))
            event_time_s = event_time_ms // 1000
            
            current_time = int(datetime.now().timestamp())
            time_until_event = event_time_s - current_time
            
            if time_until_event < self._min_seconds:
                return (
                    False,
                    f"Event in {time_until_event}s, minimum is {self._min_seconds}s"
                )
            
            return (True, None)
            
        except (ValueError, TypeError) as e:
            return (False, f"Invalid time data: {e}")
