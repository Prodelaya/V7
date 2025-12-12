"""Domain entities package.

Contains:
- Pick: A validated betting pick with all required information
- Surebet: Two betting prongs (sharp + soft) with profit
- Bookmaker: Bookmaker configuration (sharp/soft type)

Reference: docs/04-Structure.md, docs/05-Implementation.md (Phase 1)
"""

from .pick import Pick
from .surebet import Surebet
from .bookmaker import Bookmaker

__all__ = ["Pick", "Surebet", "Bookmaker"]
