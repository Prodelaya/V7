"""Pick entity representing a validated betting pick.

Implementation Requirements:
- Immutable dataclass (frozen=True)
- Contains: teams, odds, market_type, event_time, bookmaker, tournament
- Factory method: Pick.from_api_response(data)
- Redis key generation: pick.redis_key
- Reference to value objects: Odds, MarketType

Reference:
- docs/04-Structure.md: "domain/entities/"
- docs/05-Implementation.md: Task 1.7
- docs/01-SRS.md: RF-004 for Redis key format

TODO: Implement Pick entity
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

# TODO: Import value objects when implemented
# from ..value_objects.odds import Odds
# from ..value_objects.market_type import MarketType


@dataclass(frozen=True)
class Pick:
    """
    Immutable entity representing a validated betting pick.
    
    Attributes:
        teams: List of team names [team1, team2]
        odds: Betting odds value
        market_type: Type of market (over, under, win1, etc.)
        variety: Market variety/condition
        event_time: When the event starts
        bookmaker: Target bookmaker name
        tournament: Tournament/league name
        sport_id: Sport identifier
        link: URL to the bet
    
    TODO: Implement based on:
    - Task 1.7 in docs/05-Implementation.md
    - RF-004 in docs/01-SRS.md (Redis key format)
    - _get_complete_key() in legacy/RetadorV6.py (line 1012)
    """
    
    teams: List[str]
    odds: float  # TODO: Replace with Odds value object
    market_type: str  # TODO: Replace with MarketType enum
    variety: str
    event_time: datetime
    bookmaker: str
    tournament: str
    sport_id: str
    link: Optional[str] = None
    
    def __post_init__(self):
        # TODO: Add validation
        raise NotImplementedError("Pick entity not yet implemented")
    
    @classmethod
    def from_api_response(cls, data: dict) -> "Pick":
        """
        Create Pick from API response data.
        
        Args:
            data: Raw API response dict with prongs
            
        Returns:
            Validated Pick entity
            
        TODO: Implement parsing from API format
        Reference: RequestQueue.fetch_picks() in legacy/RetadorV6.py
        """
        raise NotImplementedError
    
    @property
    def redis_key(self) -> str:
        """
        Generate unique Redis key for deduplication.
        
        Format: {team1}:{team2}:{timestamp}:{market}:{variety}:{bookie}
        
        Reference: RF-004 in docs/01-SRS.md
        """
        raise NotImplementedError
    
    def get_opposite_keys(self) -> List[str]:
        """
        Generate Redis keys for opposite market picks.
        
        Used to prevent sending both sides of the same bet.
        
        Reference: _get_opposite_keys() in legacy/RetadorV6.py (line 1053)
        """
        raise NotImplementedError
