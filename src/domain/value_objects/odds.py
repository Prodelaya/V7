"""Odds value object representing betting odds.

Implementation Requirements:
- Immutable dataclass (frozen=True)
- Validation: 1.01 <= odds <= 1000.0
- Raise InvalidOddsError on invalid values
- Method: implied_probability() -> float (returns 1/value)
- Method: is_in_range(min, max) -> bool

Reference:
- docs/04-Structure.md: "value_objects/"
- docs/05-Implementation.md: Task 1.2
- docs/02-PDR.md: Section 3.1.1 (Value Objects)

TODO: Implement Odds value object
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Odds:
    """
    Immutable value object representing betting odds.
    
    Odds must be within valid range (1.01 - 1000.0).
    
    Attributes:
        value: The decimal odds value
    
    Validation (from docs/05-Implementation.md Task 1.2):
        - Odds(2.05).value == 2.05 ✅
        - Odds(1.01).value == 1.01 ✅ (minimum valid)
        - Odds(1000).value == 1000 ✅ (maximum valid)
        - Odds(0.99) → raises InvalidOddsError
        - Odds(1001) → raises InvalidOddsError
        - Odds(-1) → raises InvalidOddsError
    
    TODO: Implement based on:
    - Task 1.2 in docs/05-Implementation.md
    - Use InvalidOddsError from shared/exceptions.py
    """
    
    value: float
    
    # Configuration (can be overridden from settings)
    MIN_ODDS: float = 1.01
    MAX_ODDS: float = 1000.0
    
    def __post_init__(self):
        # TODO: Validate odds range, raise InvalidOddsError if invalid
        raise NotImplementedError("Odds value object not yet implemented")
    
    def __float__(self) -> float:
        """Allow using Odds as float."""
        return self.value
    
    def __str__(self) -> str:
        """Format odds to 2 decimal places."""
        return f"{self.value:.2f}"
    
    @property
    def implied_probability(self) -> float:
        """
        Calculate implied probability from odds.
        
        Returns:
            Probability as decimal (e.g., 0.5 for odds 2.0)
        """
        raise NotImplementedError
    
    def is_in_range(self, min_odds: float, max_odds: float) -> bool:
        """
        Check if odds are within specified range.
        
        Args:
            min_odds: Minimum acceptable odds
            max_odds: Maximum acceptable odds
            
        Returns:
            True if min_odds <= value <= max_odds
        """
        raise NotImplementedError
    
    @classmethod
    def from_probability(cls, probability: float) -> "Odds":
        """
        Create Odds from probability.
        
        Args:
            probability: Value between 0 and 1
            
        Returns:
            Odds(1/probability)
        """
        raise NotImplementedError
