"""Pick DTO for API data transformation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ...domain.entities.pick import Pick
from ...domain.value_objects.odds import Odds
from ...domain.value_objects.profit import Profit
from ...domain.value_objects.market_type import MarketType
from ...domain.services.calculation_service import CalculationService


@dataclass
class PickDTO:
    """
    Data Transfer Object for Pick data.
    
    Handles transformation from API response to domain entity.
    """
    
    id: str
    teams: tuple[str, str]
    tournament: str
    event_time: int  # Unix timestamp in milliseconds
    market_type: str
    variety: str
    soft_odds: float
    sharp_odds: float
    profit: float
    bookmaker: str
    sharp_bookmaker: str
    sport: str
    link: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: dict) -> "PickDTO":
        """Create DTO from API response data."""
        # Extract prongs
        prongs = data.get("prongs", [])
        
        # Find sharp and soft prongs
        sharp_prong = None
        soft_prong = None
        
        for prong in prongs:
            bookie = prong.get("bookie_name", "").lower()
            if bookie == "pinnaclesports":
                sharp_prong = prong
            else:
                soft_prong = prong
        
        if not sharp_prong or not soft_prong:
            raise ValueError("Invalid surebet structure: missing prong")
        
        # Extract type info from target prong
        type_info = soft_prong.get("type", {})
        
        return cls(
            id=str(data.get("id", "")),
            teams=(
                data.get("teams", ["", ""])[0],
                data.get("teams", ["", ""])[1]
            ),
            tournament=data.get("tournament", ""),
            event_time=int(data.get("time", 0)),
            market_type=type_info.get("type", ""),
            variety=type_info.get("variety", ""),
            soft_odds=float(soft_prong.get("odd", 0)),
            sharp_odds=float(sharp_prong.get("odd", 0)),
            profit=float(data.get("profit", 0)),
            bookmaker=soft_prong.get("bookie_name", ""),
            sharp_bookmaker=sharp_prong.get("bookie_name", ""),
            sport=data.get("sport", ""),
            link=soft_prong.get("link"),
        )
    
    def to_entity(self, calculation_service: CalculationService) -> Pick:
        """Convert DTO to Pick domain entity."""
        sharp_odds = Odds(self.sharp_odds)
        soft_odds = Odds(self.soft_odds)
        
        # Calculate minimum odds
        min_odds = calculation_service.calculate_min_odds(
            sharp_odds,
            self.sharp_bookmaker
        )
        
        # Convert timestamp (ms to datetime)
        event_datetime = datetime.fromtimestamp(self.event_time / 1000)
        
        return Pick(
            id=self.id,
            teams=self.teams,
            tournament=self.tournament,
            event_time=event_datetime,
            market_type=MarketType(self.market_type),
            variety=self.variety,
            odds=soft_odds,
            min_odds=min_odds,
            profit=Profit(self.profit),
            bookmaker=self.bookmaker,
            sharp_bookmaker=self.sharp_bookmaker,
            sharp_odds=sharp_odds,
            sport=self.sport,
            link=self.link,
        )
