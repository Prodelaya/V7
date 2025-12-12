"""MarketType value object representing betting market types."""

from dataclasses import dataclass
from enum import Enum
from typing import List


class Market(Enum):
    """Standard betting market types."""
    WIN1 = "win1"
    WIN2 = "win2"
    DRAW = "draw"
    OVER = "over"
    UNDER = "under"
    AH1 = "ah1"
    AH2 = "ah2"
    ODD = "odd"
    EVEN = "even"
    YES = "yes"
    NO = "no"
    _1X = "_1x"
    _X2 = "_x2"
    _12 = "_12"
    WINONLY1 = "winonly1"
    WINONLY2 = "winonly2"
    WIN1RETX = "win1retx"
    WIN2RETX = "win2retx"
    CLEAN_SHEET_1 = "clean_sheet_1"
    CLEAN_SHEET_2 = "clean_sheet_2"


# Mapping of markets to their opposites
OPPOSITE_MARKETS = {
    "win1": ["win2"],
    "win2": ["win1"],
    "over": ["under"],
    "under": ["over"],
    "ah1": ["ah2"],
    "ah2": ["ah1"],
    "odd": ["even"],
    "even": ["odd"],
    "yes": ["no"],
    "no": ["yes"],
    "_1x": ["_x2", "_12"],
    "_x2": ["_1x", "_12"],
    "_12": ["_1x", "_x2"],
    "winonly1": ["winonly2"],
    "winonly2": ["winonly1"],
    "win1retx": ["win2retx"],
    "win2retx": ["win1retx"],
    "clean_sheet_1": ["clean_sheet_2"],
    "clean_sheet_2": ["clean_sheet_1"],
}


@dataclass(frozen=True)
class MarketType:
    """
    Immutable value object representing a betting market type.
    
    Handles market type normalization and opposite market lookups.
    """
    
    value: str
    
    def __post_init__(self):
        # Normalize to lowercase
        object.__setattr__(self, "value", self.value.lower().strip())
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def opposites(self) -> List[str]:
        """Get list of opposite market types."""
        return OPPOSITE_MARKETS.get(self.value, [])
    
    def has_opposite(self) -> bool:
        """Check if market has defined opposites."""
        return self.value in OPPOSITE_MARKETS
    
    def is_opposite_of(self, other: "MarketType") -> bool:
        """Check if this market is opposite of another."""
        return other.value in self.opposites
