"""Value objects package - Immutable validated domain types.

Contains:
- Odds: Betting odds with validation (1.01-1000)
- Profit: Profit percentage with validation (-100 to 100)
- MarketType: Enum of valid market types with opposites

Reference: docs/04-Structure.md, docs/05-Implementation.md (Phase 1)
"""

from .odds import Odds
from .profit import Profit
from .market_type import MarketType

__all__ = ["Odds", "Profit", "MarketType"]
