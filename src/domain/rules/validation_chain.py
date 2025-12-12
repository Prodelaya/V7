"""Validation chain for pick validation."""

from typing import List, Tuple, Optional
from dataclasses import dataclass

from .validators.base import BaseValidator


@dataclass
class ValidationResult:
    """Result of validation chain execution."""
    is_valid: bool
    failed_validator: Optional[str] = None
    error_message: Optional[str] = None


class ValidationChain:
    """
    Chain of responsibility for pick validation.
    
    Executes validators in order, failing fast on first failure.
    """
    
    def __init__(self, validators: List[BaseValidator] = None):
        self._validators: List[BaseValidator] = validators or []
    
    def add_validator(self, validator: BaseValidator) -> "ValidationChain":
        """Add a validator to the chain."""
        self._validators.append(validator)
        return self
    
    def remove_validator(self, validator_name: str) -> "ValidationChain":
        """Remove a validator by name."""
        self._validators = [
            v for v in self._validators 
            if v.name != validator_name
        ]
        return self
    
    async def validate(self, pick_data: dict) -> ValidationResult:
        """
        Execute validation chain on pick data.
        
        Fails fast on first validation failure.
        
        Args:
            pick_data: Raw pick data to validate
            
        Returns:
            ValidationResult with status and error info if failed
        """
        for validator in self._validators:
            is_valid, error_message = await validator.validate(pick_data)
            
            if not is_valid:
                return ValidationResult(
                    is_valid=False,
                    failed_validator=validator.name,
                    error_message=error_message
                )
        
        return ValidationResult(is_valid=True)
    
    async def validate_batch(
        self, 
        picks: List[dict]
    ) -> List[Tuple[dict, ValidationResult]]:
        """
        Validate a batch of picks.
        
        Args:
            picks: List of raw pick data
            
        Returns:
            List of tuples with pick and its validation result
        """
        results = []
        for pick in picks:
            result = await self.validate(pick)
            results.append((pick, result))
        return results
    
    @property
    def validators(self) -> List[str]:
        """Get list of validator names in order."""
        return [v.name for v in self._validators]
