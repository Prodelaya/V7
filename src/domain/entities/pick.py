"""Pick entity representing a betting recommendation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..value_objects.odds import Odds
from ..value_objects.profit import Profit
from ..value_objects.market_type import MarketType


@dataclass
class Pick:
    """
    Represents a betting pick/recommendation.
    
    A pick is the final recommendation sent to users, derived from
    a surebet opportunity after validation and calculation.
    """
    
    id: str
    teams: tuple[str, str]
    tournament: str
    event_time: datetime
    market_type: MarketType
    variety: str
    odds: Odds
    min_odds: Odds
    profit: Profit
    bookmaker: str
    sharp_bookmaker: str
    sharp_odds: Odds
    sport: str
    link: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def stake_level(self) -> str:
        """Returns emoji indicator based on profit level."""
        profit_value = self.profit.value
        if profit_value < -0.5:
            return "🔴"
        elif profit_value < 1.5:
            return "🟠"
        elif profit_value < 4.0:
            return "🟡"
        return "🟢"
    
    @property
    def redis_key(self) -> str:
        """Generates unique key for Redis deduplication."""
        return (
            f"{self.teams[0]}:{self.teams[1]}:{int(self.event_time.timestamp())}:"
            f"{self.market_type.value}:{self.variety}:{self.bookmaker}"
        )
    
    def is_valid_time(self) -> bool:
        """Check if event is still in the future."""
        return self.event_time > datetime.now(self.event_time.tzinfo)
