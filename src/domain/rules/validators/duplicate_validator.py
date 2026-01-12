"""Duplicate validator - Check Redis for already-sent picks.

Checks Redis to determine if a pick or its opposite market was already sent.
This prevents duplicate sends and "rebotes" (sending both sides of a bet).

Implementation follows:
- RF-004: Deduplication with Redis
- ADR-004: Redis pipeline batch (NO Bloom Filter)
- ADR-012: NO Bloom Filter (false positives = lost picks = lost money)
- ADR-013: NO fire-and-forget (always await confirmation)

Reference:
- docs/05-Implementation.md: Task 6.2
- docs/01-SRS.md: RF-004 (deduplication)
- docs/03-ADRs.md: ADR-004, ADR-012, ADR-013
- legacy/RetadorV6.py: is_any_market_stored() (line 1077)
"""

import logging
from typing import TYPE_CHECKING, List, Protocol, runtime_checkable

from .base import BaseValidator, ValidationResult

if TYPE_CHECKING:
    from src.domain.entities.pick import Pick


logger = logging.getLogger(__name__)


@runtime_checkable
class PickRepository(Protocol):
    """Protocol for pick repository (matches RedisRepository interface).

    This protocol defines the minimal interface required for duplicate
    checking. The actual implementation is in RedisRepository.
    """

    async def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        ...

    async def exists_any(self, keys: List[str]) -> bool:
        """Check if any of the keys exist (pipeline batch)."""
        ...


class DuplicateValidator(BaseValidator):
    """Validator for duplicate/rebote detection.

    Checks Redis to determine if:
    1. This exact pick was already sent (duplicate)
    2. The opposite market was already sent (rebote)

    A "rebote" occurs when the odds flip and the opposite side becomes
    profitable. For example, if we sent OVER 2.5, we shouldn't also
    send UNDER 2.5 for the same event.

    ⚠️ NO Bloom Filter (ADR-012): 1% false positives = lost picks = lost money
    ⚠️ NO fire-and-forget (ADR-013): Race conditions cause duplicates

    Example:
        >>> repo = RedisRepository(...)
        >>> validator = DuplicateValidator(repo)
        >>> result = await validator.validate(pick)
        >>> if not result.is_valid:
        ...     print(f"Duplicate: {result.error_message}")

    Reference:
        - Task 6.2 in docs/05-Implementation.md
        - RF-004 in docs/01-SRS.md
        - ADR-004, ADR-012, ADR-013 in docs/03-ADRs.md
        - is_any_market_stored() in legacy/RetadorV6.py (line 1077)
    """

    def __init__(self, repository: PickRepository) -> None:
        """Initialize with repository.

        Args:
            repository: Repository for checking key existence.
                       Must implement PickRepository protocol
                       (e.g., RedisRepository).
        """
        self._repository = repository

    @property
    def name(self) -> str:
        """Return validator identifier."""
        return "DuplicateValidator"

    async def validate(self, pick: "Pick") -> ValidationResult:
        """Check if pick or opposite market was already sent.

        Validation flow (fail-fast):
        1. Check if exact pick key exists (duplicate)
        2. If not, check if any opposite market key exists (rebote)
        3. Return valid only if neither exists

        Args:
            pick: Pick entity to validate. Must have redis_key property
                  and get_opposite_keys() method.

        Returns:
            ValidationResult with is_valid=True if pick can be sent,
            or is_valid=False with error message if duplicate/rebote.

        Reference:
            - RF-004 in docs/01-SRS.md
            - is_any_market_stored() in legacy/RetadorV6.py
        """
        # 1. Check for exact duplicate
        main_key = pick.redis_key

        try:
            if await self._repository.exists(main_key):
                logger.debug(f"Duplicate detected: {main_key[:60]}...")
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Pick already sent: {main_key[:50]}...",
                )
        except Exception as e:
            # On Redis error, fail safely (reject pick)
            logger.error(f"Redis error checking duplicate: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Redis error checking duplicate: {e}",
            )

        # 2. Check for rebote (opposite market already sent)
        opposite_keys = pick.get_opposite_keys()

        if opposite_keys:
            try:
                if await self._repository.exists_any(opposite_keys):
                    logger.debug(
                        f"Rebote detected for {pick.market_type.value}: "
                        f"opposite market already sent"
                    )
                    return ValidationResult(
                        is_valid=False,
                        error_message="Opposite market already sent (rebote)",
                    )
            except Exception as e:
                # On Redis error, fail safely (reject pick)
                logger.error(f"Redis error checking rebote: {e}")
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Redis error checking rebote: {e}",
                )

        # 3. Not a duplicate, validation passes
        return ValidationResult(is_valid=True)
