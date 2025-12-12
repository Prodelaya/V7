"""Bookmaker entity representing a betting house."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class BookmakerType(Enum):
    """Type of bookmaker based on odds efficiency."""
    SHARP = "sharp"
    SOFT = "soft"


@dataclass
class Bookmaker:
    """
    Represents a bookmaker/betting house.
    
    Sharps have efficient odds (low margin), while softs have
    inflated odds that can offer value opportunities.
    """
    
    id: str
    name: str
    type: BookmakerType
    telegram_channel_id: Optional[int] = None
    allowed_counterparts: List[str] = None
    
    def __post_init__(self):
        if self.allowed_counterparts is None:
            self.allowed_counterparts = []
    
    @property
    def is_sharp(self) -> bool:
        """Check if bookmaker is a sharp."""
        return self.type == BookmakerType.SHARP
    
    @property
    def is_soft(self) -> bool:
        """Check if bookmaker is a soft."""
        return self.type == BookmakerType.SOFT
    
    def can_use_counterpart(self, counterpart_id: str) -> bool:
        """Check if a counterpart bookmaker is allowed."""
        if not self.allowed_counterparts:
            return True
        return counterpart_id.lower() in [c.lower() for c in self.allowed_counterparts]
