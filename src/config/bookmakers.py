"""Bookmaker configuration."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..domain.entities.bookmaker import Bookmaker, BookmakerType


@dataclass
class BookmakerConfig:
    """
    Configuration for bookmakers and their relationships.
    
    Defines which bookmakers are sharps, softs, and their
    allowed counterparts.
    """
    
    # Sharp bookmakers (reference odds)
    sharps: List[Bookmaker] = field(default_factory=lambda: [
        Bookmaker(
            id="pinnaclesports",
            name="Pinnacle Sports",
            type=BookmakerType.SHARP,
        ),
    ])
    
    # Soft bookmakers (target for betting)
    softs: List[Bookmaker] = field(default_factory=lambda: [
        Bookmaker(
            id="retabet_apuestas",
            name="Retabet",
            type=BookmakerType.SOFT,
            telegram_channel_id=-1002294438792,
            allowed_counterparts=["pinnaclesports"],
        ),
        Bookmaker(
            id="yaasscasino",
            name="Yaass Casino",
            type=BookmakerType.SOFT,
            telegram_channel_id=-1002360901387,
            allowed_counterparts=["pinnaclesports"],
        ),
    ])
    
    @property
    def all_bookmakers(self) -> List[Bookmaker]:
        """Get all configured bookmakers."""
        return self.sharps + self.softs
    
    @property
    def bookmaker_ids(self) -> List[str]:
        """Get all bookmaker IDs for API query."""
        return [b.id for b in self.all_bookmakers]
    
    @property
    def soft_ids(self) -> List[str]:
        """Get soft bookmaker IDs."""
        return [b.id for b in self.softs]
    
    @property
    def channel_mapping(self) -> Dict[str, int]:
        """Get bookmaker to channel ID mapping."""
        return {
            b.id: b.telegram_channel_id
            for b in self.softs
            if b.telegram_channel_id
        }
    
    def get_bookmaker(self, bookmaker_id: str) -> Optional[Bookmaker]:
        """Get bookmaker by ID."""
        for bookmaker in self.all_bookmakers:
            if bookmaker.id.lower() == bookmaker_id.lower():
                return bookmaker
        return None
    
    def is_valid_pair(self, soft_id: str, sharp_id: str) -> bool:
        """Check if soft/sharp pair is valid."""
        soft = self.get_bookmaker(soft_id)
        if not soft or soft.is_sharp:
            return False
        return soft.can_use_counterpart(sharp_id)
