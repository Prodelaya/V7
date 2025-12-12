"""Surebet entity representing an arbitrage opportunity.

Implementation Requirements:
- Contains two prongs: sharp (Pinnacle) and soft (target bookmaker)
- Calculates profit from the two prongs
- Determines which prong is sharp vs soft based on bookmaker hierarchy

Reference:
- docs/04-Structure.md: "domain/entities/"
- docs/05-Implementation.md: Task 1.8
- docs/01-SRS.md: Section 2.2 (Business Model)
- docs/02-PDR.md: Section 3.1.2 (Entities)

TODO: Implement Surebet entity
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

from .pick import Pick


@dataclass(frozen=True)
class Prong:
    """
    Represents one side of a surebet.
    
    Attributes:
        bookmaker: Bookmaker identifier
        odds: Betting odds
        market_type: Market type
        variety: Market variety/condition
    """
    bookmaker: str
    odds: float
    market_type: str
    variety: str


@dataclass(frozen=True)
class Surebet:
    """
    Represents a surebet (arbitrage opportunity) between two bookmakers.
    
    A surebet consists of:
    - prong_sharp: The side at the sharp bookmaker (Pinnacle)
    - prong_soft: The side at the soft bookmaker (target)
    - profit: Calculated profit percentage
    
    TODO: Implement based on:
    - Task 1.8 in docs/05-Implementation.md
    - Section 2.2 in docs/01-SRS.md
    - determine_bet_roles() in legacy/RetadorV6.py
    """
    
    prong_sharp: Prong
    prong_soft: Prong
    profit: float
    teams: tuple
    event_time: int
    tournament: str
    sport_id: str
    
    def __post_init__(self):
        # TODO: Add validation
        raise NotImplementedError("Surebet entity not yet implemented")
    
    @classmethod
    def from_api_response(cls, data: dict) -> Optional["Surebet"]:
        """
        Create Surebet from API response.
        
        Must determine which prong is sharp and which is soft
        based on bookmaker hierarchy.
        
        Args:
            data: Raw API response with 'prongs' array
            
        Returns:
            Surebet entity or None if invalid
            
        Reference: determine_bet_roles() in legacy/RetadorV6.py
        """
        raise NotImplementedError
    
    def to_pick(self) -> Pick:
        """
        Convert to Pick entity (the soft prong becomes the pick).
        
        Returns:
            Pick entity for the soft side
        """
        raise NotImplementedError
