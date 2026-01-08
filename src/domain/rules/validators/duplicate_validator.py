"""Duplicate validator - Check Redis for already-sent picks.

Implementation Requirements:
- Check if pick key exists in Redis
- Check if opposite market was sent (rebote detection)
- I/O operation (Redis)
- Use repository pattern (inject repository)

Reference:
- docs/05-Implementation.md: Task 6.2
- docs/01-SRS.md: RF-004 (deduplication)
- docs/03-ADRs.md: ADR-004 (No Bloom Filter)

TODO: Implement DuplicateValidator
"""

from typing import Optional, Protocol, Tuple

from .base import BaseValidator


class PickRepository(Protocol):
    """Protocol for pick repository."""
    async def exists(self, key: str) -> bool: ...
    async def exists_any(self, keys: list) -> bool: ...


class DuplicateValidator(BaseValidator):
    """
    Validator for duplicate/rebote detection.

    Checks Redis to determine if:
    1. This exact pick was already sent
    2. The opposite market was already sent (rebote)

    ⚠️ NO Bloom Filter (from ADR-012 - false positives lose picks)
    ⚠️ NO fire-and-forget (from ADR-013 - race conditions)

    TODO: Implement based on:
    - Task 6.2 in docs/05-Implementation.md
    - RF-004 in docs/01-SRS.md
    - ADR-004 in docs/03-ADRs.md
    - is_any_market_stored() in legacy/RetadorV6.py (line 1077)
    """

    def __init__(self, repository: PickRepository):
        """
        Initialize with repository.

        Args:
            repository: Repository for checking existence
        """
        self._repository = repository

    @property
    def name(self) -> str:
        return "DuplicateValidator"

    async def validate(self, pick_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if pick or opposite was already sent.

        Args:
            pick_data: Must contain data to generate Redis key

        Returns:
            (True, None) if NOT duplicate (can send)
            (False, "message") if duplicate or rebote

        Reference: RF-004 in docs/01-SRS.md
        """
        raise NotImplementedError("DuplicateValidator.validate not implemented")
