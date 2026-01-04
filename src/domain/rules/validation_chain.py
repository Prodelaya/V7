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
"""

from dataclasses import dataclass
from typing import List, Optional, Union

from src.domain.entities.pick import Pick
from src.domain.entities.surebet import Surebet

from .validators.base import BaseValidator
from .validators.profit_validator import ProfitValidator


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Result of validation chain execution.

    Attributes:
        is_valid: True if all validators passed
        error_message: Description of failure (if any)
        failed_validator: Name of validator that failed (if any)

    Examples:
        >>> result = ValidationResult(is_valid=True)
        >>> result.is_valid
        True

        >>> result = ValidationResult(
        ...     is_valid=False,
        ...     error_message="Odds too low",
        ...     failed_validator="OddsValidator"
        ... )
        >>> result.failed_validator
        'OddsValidator'
    """
    is_valid: bool
    error_message: Optional[str] = None
    failed_validator: Optional[str] = None


class ValidationChain:
    """
    Chain of Responsibility for pick validation.

    Executes validators in order, stopping at first failure (fail-fast).
    Uses composition over set_next() for flexibility (from base.py design).

    Validation order (from docs/03-ADRs.md ADR-005):
        1. OddsValidator (CPU, ~0ms)
        2. ProfitValidator (CPU, ~0ms)
        3. TimeValidator (CPU, ~0ms)
        4. DuplicateValidator (I/O Redis, ~5ms) - added later in Fase 6

    Example:
        >>> chain = ValidationChain.create_default()
        >>> result = await chain.validate(surebet)
        >>> if not result.is_valid:
        ...     print(f"Failed: {result.failed_validator}: {result.error_message}")

    Reference:
        - Task 3.5 in docs/05-Implementation.md
        - ADR-005 in docs/03-ADRs.md
    """

    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        """
        Initialize validation chain.

        Args:
            validators: List of validators in execution order.
                       Order matters: CPU-bound first, I/O last.
        """
        self._validators: List[BaseValidator] = list(validators) if validators else []

    @property
    def validators(self) -> List[BaseValidator]:
        """Return copy of validators list to prevent external mutation."""
        return list(self._validators)

    @property
    def is_empty(self) -> bool:
        """Check if chain has no validators."""
        return len(self._validators) == 0

    def __len__(self) -> int:
        """Return number of validators in chain."""
        return len(self._validators)

    def add_validator(self, validator: BaseValidator) -> None:
        """
        Add a validator to the end of the chain.

        Args:
            validator: Validator to add

        Note:
            Validators are executed in order of addition.
            Add CPU-bound validators first, I/O validators last.
        """
        self._validators.append(validator)

    def remove_validator(self, name: str) -> bool:
        """
        Remove validator by name.

        Args:
            name: Name of validator to remove (as returned by validator.name)

        Returns:
            True if validator was found and removed, False otherwise.
        """
        for i, validator in enumerate(self._validators):
            if validator.name == name:
                self._validators.pop(i)
                return True
        return False

    async def validate(self, data: Union[Pick, Surebet]) -> ValidationResult:
        """
        Run all validators on data.

        Stops at first failure (fail-fast).

        Args:
            data: Pick or Surebet entity to validate.
                  If Surebet, extracts Pick for validators that need it.

        Returns:
            ValidationResult indicating success or failure.
            On failure, includes failed_validator name and error_message.

        Example:
            >>> result = await chain.validate(surebet)
            >>> result.is_valid
            False
            >>> result.failed_validator
            'OddsValidator'

        Reference: RF-003 in docs/01-SRS.md
        """
        # Empty chain always passes
        if not self._validators:
            return ValidationResult(is_valid=True)

        # Prepare Pick and Surebet for validators
        if isinstance(data, Surebet):
            pick = data.to_pick()
            surebet = data
        else:
            pick = data
            surebet = None

        # Execute validators in order (fail-fast)
        for validator in self._validators:
            # ProfitValidator needs Surebet specifically
            if isinstance(validator, ProfitValidator):
                if surebet is None:
                    # Cannot validate profit without Surebet, skip
                    continue
                result = await validator.validate(surebet)
            else:
                # Other validators use Pick
                result = await validator.validate(pick)

            # Fail-fast: stop on first failure
            if not result.is_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message=result.error_message,
                    failed_validator=validator.name,
                )

        # All validators passed
        return ValidationResult(is_valid=True)

    @classmethod
    def create_default(cls) -> "ValidationChain":
        """
        Create chain with default CPU-only validators.

        Order (from ADR-005):
            1. OddsValidator (min_odds=1.10, max_odds=9.99)
            2. ProfitValidator (min_profit=-1.0, max_profit=25.0)
            3. TimeValidator (min_seconds=0)

        Note:
            DuplicateValidator must be added separately when repository
            is available (Task 6.2 in Fase 6).

        Returns:
            Configured ValidationChain with CPU-only validators.
        """
        from .validators import OddsValidator, ProfitValidator, TimeValidator

        return cls([
            OddsValidator(),  # min_odds=1.10, max_odds=9.99
            ProfitValidator(),  # min_profit=-1.0, max_profit=25.0
            TimeValidator(),  # min_seconds=0
        ])
