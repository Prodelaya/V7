"""Profit value object representing surebet profit percentage.

Implementation Requirements:
- Immutable dataclass (frozen=True)
- Validation: -100 <= profit <= 100
- Method: is_acceptable() -> bool (checks if within trading range)
- Trading range: -1% to 25% (from docs/01-SRS.md RF-003)

Reference:
- docs/04-Structure.md: "value_objects/"
- docs/05-Implementation.md: Task 1.3
- docs/02-PDR.md: Section 3.1.1 (Value Objects)

TODO: Implement Profit value object
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Profit:
    """
    Immutable value object representing profit percentage.
    
    Profit is stored as a percentage (e.g., 2.5 means 2.5%).
    
    Attributes:
        value: Profit percentage
    
    Validation (from docs/05-Implementation.md Task 1.3):
        - Profit(2.5).value == 2.5 ✅
        - Profit(150) → raises InvalidProfitError
        - Profit(-150) → raises InvalidProfitError
    
    Acceptable range for trading (from docs/01-SRS.md RF-003):
        - Minimum: -1%
        - Maximum: 25%
    
    TODO: Implement based on:
    - Task 1.3 in docs/05-Implementation.md
    - RF-003 in docs/01-SRS.md
    - Use InvalidProfitError from shared/exceptions.py
    """
    
    value: float
    
    # Absolute limits
    MIN_VALUE: float = -100.0
    MAX_VALUE: float = 100.0
    
    # Trading limits (from SRS RF-003)
    MIN_ACCEPTABLE: float = -1.0
    MAX_ACCEPTABLE: float = 25.0
    
    def __post_init__(self):
        # TODO: Validate profit range, raise InvalidProfitError if invalid
        raise NotImplementedError("Profit value object not yet implemented")
    
    def __float__(self) -> float:
        """Allow using Profit as float."""
        return self.value
    
    def __str__(self) -> str:
        """Format profit as percentage."""
        return f"{self.value:.2f}%"
    
    def is_acceptable(self) -> bool:
        """
        Check if profit is within acceptable trading range.
        
        Returns:
            True if -1% <= value <= 25%
        
        Reference: RF-003 in docs/01-SRS.md
        """
        raise NotImplementedError
    
    @property
    def as_decimal(self) -> float:
        """
        Convert percentage to decimal.
        
        Returns:
            Profit as decimal (e.g., 0.025 for 2.5%)
        """
        raise NotImplementedError
