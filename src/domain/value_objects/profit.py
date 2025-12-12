"""Profit value object representing surebet profit percentage."""

from dataclasses import dataclass
from enum import Enum


class ProfitLevel(Enum):
    """Profit level categories for stake recommendation."""
    LOW = "low"
    MEDIUM_LOW = "medium_low"
    MEDIUM_HIGH = "medium_high"
    HIGH = "high"


@dataclass(frozen=True)
class Profit:
    """
    Immutable value object representing profit percentage.
    
    Profit is the theoretical gain from a surebet, expressed
    as a percentage (-1% to 25% typically).
    """
    
    value: float  # Percentage value (e.g., 2.5 for 2.5%)
    
    MIN_PROFIT = -10.0
    MAX_PROFIT = 100.0
    
    def __post_init__(self):
        if not self.MIN_PROFIT <= self.value <= self.MAX_PROFIT:
            raise ValueError(
                f"Profit must be between {self.MIN_PROFIT}% and {self.MAX_PROFIT}%, "
                f"got {self.value}%"
            )
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.2f}%"
    
    @property
    def level(self) -> ProfitLevel:
        """Get profit level category."""
        if self.value < -0.5:
            return ProfitLevel.LOW
        elif self.value < 1.5:
            return ProfitLevel.MEDIUM_LOW
        elif self.value < 4.0:
            return ProfitLevel.MEDIUM_HIGH
        return ProfitLevel.HIGH
    
    @property
    def emoji(self) -> str:
        """Get emoji indicator for profit level."""
        level_emojis = {
            ProfitLevel.LOW: "🔴",
            ProfitLevel.MEDIUM_LOW: "🟠",
            ProfitLevel.MEDIUM_HIGH: "🟡",
            ProfitLevel.HIGH: "🟢",
        }
        return level_emojis[self.level]
    
    def is_acceptable(self, min_profit: float = -1.0, max_profit: float = 25.0) -> bool:
        """Check if profit is within acceptable range."""
        return min_profit <= self.value <= max_profit
