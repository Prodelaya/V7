"""Pick Data Transfer Object for API/domain conversion.

Implementation Requirements:
- Parse raw API response into structured data
- Convert to domain entities (Pick, Surebet)
- Handle prong role determination (sharp vs soft)

Reference:
- docs/05-Implementation.md: Task 6.1
- docs/04-Structure.md: "application/dto/"

TODO: Implement PickDTO
"""

from dataclasses import dataclass
from typing import List, Optional

# from ...domain.entities.pick import Pick
# from ...domain.entities.surebet import Surebet


@dataclass
class PickDTO:
    """
    Data Transfer Object for converting API data to domain entities.

    Handles the complex structure of API responses:
    - prongs array with bookmaker data
    - type dict with market info
    - Determining sharp vs soft roles

    TODO: Implement based on:
    - Task 6.1 in docs/05-Implementation.md
    - API response structure in legacy/RetadorV6.py
    """

    # Raw data fields
    teams: List[str]
    event_time: int
    profit: float
    tournament: str
    sport_id: str

    # Prong data
    sharp_bookmaker: str
    sharp_odds: float
    soft_bookmaker: str
    soft_odds: float

    # Market info
    market_type: str
    variety: str
    condition: Optional[str] = None
    period: Optional[str] = None

    # Links
    link: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "PickDTO":
        """
        Create DTO from raw API response.

        Must determine which prong is sharp and which is soft
        based on bookmaker hierarchy.

        Args:
            data: Raw API response with 'prongs' array

        Returns:
            PickDTO instance

        Reference:
        - determine_bet_roles() logic in legacy/RetadorV6.py
        - BOOKIE_HIERARCHY in BotConfig
        """
        raise NotImplementedError("PickDTO.from_api_response not implemented")

    def to_entity(self):  # -> Pick:
        """
        Convert DTO to domain Pick entity.

        Returns:
            Pick domain entity
        """
        raise NotImplementedError("PickDTO.to_entity not implemented")

    def to_surebet(self):  # -> Surebet:
        """
        Convert DTO to domain Surebet entity.

        Returns:
            Surebet domain entity
        """
        raise NotImplementedError("PickDTO.to_surebet not implemented")
