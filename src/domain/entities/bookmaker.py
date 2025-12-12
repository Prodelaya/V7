"""Bookmaker entity representing a betting house.

Implementation Requirements:
- Enum for bookmaker type: SHARP or SOFT
- Configuration for each bookmaker (name, type, channels)
- Reference sharp list: pinnaclesports
- Reference soft list: retabet_apuestas, yaasscasino, etc.

Reference:
- docs/04-Structure.md: "domain/entities/"
- docs/05-Implementation.md: Task 1.6
- legacy/RetadorV6.py: BotConfig.BOOKIE_HIERARCHY, TARGET_BOOKIES

TODO: Implement Bookmaker entity
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BookmakerType(Enum):
    """Type of bookmaker."""
    SHARP = "sharp"
    SOFT = "soft"


@dataclass(frozen=True)
class Bookmaker:
    """
    Represents a bookmaker/betting house.
    
    Attributes:
        name: Internal identifier (e.g., "pinnaclesports", "retabet_apuestas")
        type: SHARP or SOFT classification
        display_name: Human-readable name
        channel_id: Optional Telegram channel ID for this bookmaker
    
    TODO: Implement based on:
    - Task 1.6 in docs/05-Implementation.md
    - BotConfig in legacy/RetadorV6.py (lines 250-360)
    """
    
    name: str
    type: BookmakerType
    display_name: Optional[str] = None
    channel_id: Optional[int] = None
    
    def __post_init__(self):
        # TODO: Add validation
        raise NotImplementedError("Bookmaker entity not yet implemented")
    
    @property
    def is_sharp(self) -> bool:
        """Check if bookmaker is a sharp."""
        raise NotImplementedError
    
    @property
    def is_soft(self) -> bool:
        """Check if bookmaker is a soft."""
        raise NotImplementedError
