"""Odds value object representing betting odds."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Odds:
    """
    Immutable value object representing betting odds.
    
    Odds must be within valid range (1.01 - 1000.0).
    """
    
    value: float
    
    MIN_ODDS = 1.01
    MAX_ODDS = 1000.0
    
    def __post_init__(self):
        if not self.MIN_ODDS <= self.value <= self.MAX_ODDS:
            raise ValueError(
                f"Odds must be between {self.MIN_ODDS} and {self.MAX_ODDS}, "
                f"got {self.value}"
            )
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.2f}"
    
    @property
    def implied_probability(self) -> float:
        """Calculate implied probability from odds."""
        return 1 / self.value
    
    def is_in_range(self, min_odds: float, max_odds: float) -> bool:
        """Check if odds are within specified range."""
        return min_odds <= self.value <= max_odds
    
    @classmethod
    def from_probability(cls, probability: float) -> "Odds":
        """Create Odds from probability."""
        if not 0 < probability < 1:
            raise ValueError("Probability must be between 0 and 1")
        return cls(1 / probability)
