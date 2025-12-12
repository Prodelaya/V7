"""Surebet entity representing an arbitrage opportunity."""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Prong:
    """Represents one side/leg of a surebet."""
    
    bookmaker: str
    odds: float
    market_type: str
    variety: str
    link: str


@dataclass
class Surebet:
    """
    Represents a surebet/arbitrage opportunity from the API.
    
    A surebet consists of two prongs (legs) where betting both
    sides guarantees a profit or minimal loss.
    """
    
    id: str
    teams: tuple[str, str]
    tournament: str
    sport: str
    event_time: datetime
    profit: float
    prongs: List[Prong]
    created_at: datetime
    
    @property
    def sharp_prong(self) -> Prong | None:
        """Returns the prong from the sharp bookmaker (Pinnacle)."""
        for prong in self.prongs:
            if prong.bookmaker.lower() == "pinnaclesports":
                return prong
        return None
    
    @property
    def soft_prong(self) -> Prong | None:
        """Returns the prong from the soft bookmaker."""
        for prong in self.prongs:
            if prong.bookmaker.lower() != "pinnaclesports":
                return prong
        return None
    
    def has_valid_structure(self) -> bool:
        """Check if surebet has exactly 2 prongs with one sharp."""
        return len(self.prongs) == 2 and self.sharp_prong is not None
