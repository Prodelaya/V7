"""Domain entities package.

Contains:
- Pick: A validated betting pick with all required information
- Surebet: Two betting prongs (sharp + soft) with profit
- Bookmaker: Bookmaker configuration (sharp/soft type)
- SHARP_BOOKMAKERS: Set of recognized sharp bookmaker names

Reference: docs/04-Structure.md, docs/05-Implementation.md (Phase 1)
"""

from .bookmaker import Bookmaker, BookmakerType
from .pick import Pick
from .surebet import SHARP_BOOKMAKERS, Surebet

__all__ = ["Pick", "Surebet", "Bookmaker", "BookmakerType", "SHARP_BOOKMAKERS"]
