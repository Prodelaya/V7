"""Calculators package - Strategy pattern for sharp-specific calculations.

Contains:
- base: Abstract base class, result dataclasses, and default constants
- pinnacle: Pinnacle-specific calculator
- factory: Factory to get calculator by bookmaker name (with DI)

Design:
- Profit limits are injected via factory from Settings/.env
- Each calculator receives limits in __init__ (Dependency Injection)

Reference: docs/02-PDR.md Section 4.1, docs/05-Implementation.md Phase 2
"""

from .base import (
    DEFAULT_MAX_PROFIT,
    DEFAULT_MIN_PROFIT,
    BaseCalculator,
    MinOddsResult,
    StakeResult,
)
from .factory import CalculatorFactory
from .pinnacle import PinnacleCalculator

__all__ = [
    # Base classes and dataclasses
    "BaseCalculator",
    "StakeResult",
    "MinOddsResult",
    # Implementations
    "PinnacleCalculator",
    "CalculatorFactory",
    # Constants (for external configuration)
    "DEFAULT_MIN_PROFIT",
    "DEFAULT_MAX_PROFIT",
]
