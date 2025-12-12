"""Validation chain implementing Chain of Responsibility pattern.

Implementation Requirements:
- Chain multiple validators in order
- Fail-fast: stop on first failure
- Return ValidationResult with is_valid, error_message, failed_validator
- Order validators by cost (CPU first, I/O last)

Reference:
- docs/02-PDR.md: Section 4.2 (Chain of Responsibility)
- docs/05-Implementation.md: Task 3.5
- docs/03-ADRs.md: ADR-005
- docs/01-SRS.md: RF-003 (validation requirements)

TODO: Implement ValidationChain
"""

from dataclasses import dataclass
from typing import List, Optional

from .validators.base import BaseValidator


@dataclass
class ValidationResult:
    """
    Result of validation chain execution.
    
    Attributes:
        is_valid: True if all validators passed
        error_message: Description of failure (if any)
        failed_validator: Name of validator that failed (if any)
    """
    is_valid: bool
    error_message: Optional[str] = None
    failed_validator: Optional[str] = None


class ValidationChain:
    """
    Chain of Responsibility for pick validation.
    
    Executes validators in order, stopping at first failure (fail-fast).
    
    Validation order (from docs/03-ADRs.md ADR-005):
        1. OddsValidator (CPU, ~0ms)
        2. ProfitValidator (CPU, ~0ms)
        3. TimeValidator (CPU, ~0ms)
        4. DuplicateValidator (I/O Redis, ~5ms)
        5. OppositeMarketValidator (I/O Redis, ~5ms)
    
    TODO: Implement based on:
    - Task 3.5 in docs/05-Implementation.md
    - ADR-005 in docs/03-ADRs.md
    """
    
    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        """
        Initialize validation chain.
        
        Args:
            validators: List of validators in execution order
        """
        self._validators = validators or []
    
    def add_validator(self, validator: BaseValidator) -> None:
        """
        Add a validator to the chain.
        
        Args:
            validator: Validator to add
        """
        raise NotImplementedError("ValidationChain.add_validator not implemented")
    
    async def validate(self, pick_data: dict) -> ValidationResult:
        """
        Run all validators on pick data.
        
        Stops at first failure (fail-fast).
        
        Args:
            pick_data: Raw pick data from API
            
        Returns:
            ValidationResult indicating success or failure
        
        Reference: RF-003 in docs/01-SRS.md
        """
        raise NotImplementedError("ValidationChain.validate not implemented")
    
    @classmethod
    def create_default(cls) -> "ValidationChain":
        """
        Create chain with default validators in correct order.
        
        Order (from ADR-005):
            1. OddsValidator
            2. ProfitValidator
            3. TimeValidator
            4. DuplicateValidator
            5. OppositeMarketValidator
        
        Returns:
            Configured ValidationChain
        """
        raise NotImplementedError("ValidationChain.create_default not implemented")
