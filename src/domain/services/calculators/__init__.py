"""Calculators package - Strategy pattern for sharp-specific calculations.

Contains:
- base: Abstract base class and result dataclasses
- pinnacle: Pinnacle-specific calculator
- factory: Factory to get calculator by bookmaker name

Reference: docs/02-PDR.md Section 4.1, docs/05-Implementation.md Phase 2
"""

from .base import BaseCalculator, StakeResult, MinOddsResult
from .pinnacle import PinnacleCalculator
from .factory import CalculatorFactory

__all__ = [
    "BaseCalculator", 
    "StakeResult", 
    "MinOddsResult",
    "PinnacleCalculator", 
    "CalculatorFactory"
]
