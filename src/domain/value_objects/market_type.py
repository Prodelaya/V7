"""MarketType enum representing betting market types.

Implementation Requirements:
- Enum with predefined market types
- Method: get_opposites() -> List[MarketType]
- Mapping of opposite markets for rebote detection

Reference:
- docs/04-Structure.md: "value_objects/"
- docs/05-Implementation.md: Task 1.4
- docs/01-SRS.md: Appendix 6.1 (Opposite Markets)
- legacy/RetadorV6.py: opposite_markets dict (line 880)

TODO: Implement MarketType enum
"""

from enum import Enum
from typing import List


class MarketType(Enum):
    """
    Enum of valid betting market types.
    
    Markets with opposites (from docs/01-SRS.md Appendix 6.1):
        - win1 ↔ win2
        - over ↔ under
        - ah1 ↔ ah2
        - odd ↔ even
        - yes ↔ no
        - _1x ↔ _x2, _12
    
    TODO: Implement based on:
    - Task 1.4 in docs/05-Implementation.md
    - Appendix 6.1 in docs/01-SRS.md
    - opposite_markets in legacy/RetadorV6.py (line 880)
    """
    
    # Money line / Match winner
    WIN1 = "win1"
    WIN2 = "win2"
    DRAW = "draw"
    
    # Double chance
    _1X = "_1x"
    _X2 = "_x2"
    _12 = "_12"
    
    # Totals
    OVER = "over"
    UNDER = "under"
    
    # Asian handicap
    AH1 = "ah1"
    AH2 = "ah2"
    
    # Odd/Even
    ODD = "odd"
    EVEN = "even"
    
    # Yes/No (BTTS, etc.)
    YES = "yes"
    NO = "no"
    
    # Draw no bet
    WIN1RETX = "win1retx"
    WIN2RETX = "win2retx"
    
    # Win only
    WINONLY1 = "winonly1"
    WINONLY2 = "winonly2"
    
    # TODO: Add more market types as needed
    
    def get_opposites(self) -> List["MarketType"]:
        """
        Get opposite market types for this market.
        
        Used for rebote detection - we don't send both sides
        of the same bet.
        
        Returns:
            List of opposite MarketType values
        
        Reference: Appendix 6.1 in docs/01-SRS.md
        """
        raise NotImplementedError("MarketType.get_opposites not yet implemented")
    
    @classmethod
    def from_string(cls, value: str) -> "MarketType":
        """
        Create MarketType from string (case-insensitive).
        
        Args:
            value: Market type string from API
            
        Returns:
            Matching MarketType enum value
            
        Raises:
            ValueError: If no matching market type
        """
        raise NotImplementedError


# Opposite markets mapping (from docs/01-SRS.md Appendix 6.1)
# TODO: Use this mapping in get_opposites()
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
    # Add more from legacy/RetadorV6.py line 880
}
