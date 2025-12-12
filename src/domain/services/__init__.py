"""Domain services package.

Contains:
- calculation_service: Orchestrates stake and min_odds calculations
- opposite_market_service: Resolves opposite markets
- calculators/: Strategy pattern implementations for each sharp

Reference: docs/04-Structure.md, docs/02-PDR.md Section 3.1.3
"""

from .calculation_service import CalculationService
from .opposite_market_service import OppositeMarketService

__all__ = ["CalculationService", "OppositeMarketService"]
