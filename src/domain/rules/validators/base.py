"""Base validator for Chain of Responsibility pattern (ADR-005).

Implements the abstract base class for pick validators. Validators are
stateless and composed via ValidationChain for fail-fast execution.

Design Decisions:
- Uses Pick entity for type safety (not dict)
- Composition over set_next() for flexibility
- Async validate() to support I/O validators (Redis)

Validation Order (ADR-005 - CPU first, I/O last):
    1. OddsValidator (CPU, ~0ms)
    2. ProfitValidator (CPU, ~0ms)
    3. TimeValidator (CPU, ~0ms)
    4. DuplicateValidator (I/O Redis, ~5ms)

Reference:
- docs/02-PDR.md: Section 6.3 (Validator interface)
- docs/03-ADRs.md: ADR-005 (validation order)
- docs/05-Implementation.md: Task 3.1
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.domain.entities.pick import Pick


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of a single validation check.
    
    Attributes:
        is_valid: True if validation passed
        error_message: Human-readable failure reason, or None if valid
    
    Examples:
        >>> result = ValidationResult(is_valid=True)
        >>> result.is_valid
        True
        
        >>> result = ValidationResult(is_valid=False, error_message="Odds too low")
        >>> result.error_message
        'Odds too low'
    """
    is_valid: bool
    error_message: Optional[str] = None


class BaseValidator(ABC):
    """Abstract base class for pick validators.
    
    Each validator checks one specific validation rule and returns
    a ValidationResult. Validators are stateless and composable.
    
    The ValidationChain orchestrates execution order (fail-fast):
    CPU-bound validators first, I/O validators last.
    
    Example:
        >>> class OddsValidator(BaseValidator):
        ...     @property
        ...     def name(self) -> str:
        ...         return "OddsValidator"
        ...     
        ...     async def validate(self, pick: Pick) -> ValidationResult:
        ...         if pick.odds.value < 1.10:
        ...             return ValidationResult(False, "Odds below minimum 1.10")
        ...         return ValidationResult(True)
    
    Reference:
        - ADR-005 in docs/03-ADRs.md (validation chain order)
        - Task 3.1 in docs/05-Implementation.md
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier for this validator.
        
        Used in ValidationResult.failed_validator and logging.
        
        Returns:
            Validator class name (e.g., "OddsValidator")
        """
        pass
    
    @abstractmethod
    async def validate(self, pick: Pick) -> ValidationResult:
        """Validate pick against this validator's rule.
        
        This method is async to support I/O validators (e.g., Redis lookup).
        CPU-only validators are still async for interface consistency.
        
        Args:
            pick: Pick entity to validate
        
        Returns:
            ValidationResult with is_valid and optional error_message
        """
        pass
