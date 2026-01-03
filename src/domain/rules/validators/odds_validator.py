"""Odds validator - OPTIONAL SAFETY CHECK for odds range.

This validator is OPTIONAL since ADR-015 implements origin filtering:
- API parameter `min-odds=1.10` already filters minimum odds
- API parameter `max-odds=9.99` already filters maximum odds

Keep as safety check in case:
- API parameters change or fail silently
- Configuration mismatch between API params and validator

Implementation Requirements:
- Validate odds between MIN_ODDS (1.10) and MAX_ODDS (9.99)
- CPU-only operation (no I/O) - ~0ms overhead

Reference:
- docs/03-ADRs.md: ADR-015 (Origin Filtering)
- docs/05-Implementation.md: Task 3.2
- docs/01-SRS.md: RF-003 (validation requirements)
"""

from src.domain.entities.pick import Pick

from .base import BaseValidator, ValidationResult


class OddsValidator(BaseValidator):
    """OPTIONAL SAFETY CHECK: Validator for betting odds range.

    Since ADR-015, the API filters odds at origin with min-odds/max-odds.
    This validator serves as a redundant safety check (~0ms overhead).

    Can be disabled in validation chain if full trust in API is desired.

    Checks that odds are within configured range:
    - Minimum: 1.10 (default, from SRS)
    - Maximum: 9.99 (default, from SRS)

    Example:
        >>> validator = OddsValidator(min_odds=1.10, max_odds=9.99)
        >>> result = await validator.validate(pick)
        >>> result.is_valid
        True

    Reference:
        - ADR-015 in docs/03-ADRs.md (Origin Filtering)
        - Task 3.2 in docs/05-Implementation.md
        - RF-003 in docs/01-SRS.md
    """

    def __init__(self, min_odds: float = 1.10, max_odds: float = 9.99):
        """Initialize with odds range.

        Args:
            min_odds: Minimum acceptable odds (default 1.10)
            max_odds: Maximum acceptable odds (default 9.99)

        Raises:
            ValueError: If min_odds >= max_odds
        """
        if min_odds >= max_odds:
            raise ValueError(
                f"min_odds ({min_odds}) must be less than max_odds ({max_odds})"
            )
        self._min_odds = min_odds
        self._max_odds = max_odds

    @property
    def name(self) -> str:
        """Return validator identifier."""
        return "OddsValidator"

    async def validate(self, pick: Pick) -> ValidationResult:
        """Check if pick odds are within configured range.

        Uses the Odds value object's is_in_range() method for validation.
        This is a CPU-only operation with ~0ms overhead.

        Args:
            pick: Pick entity to validate

        Returns:
            ValidationResult with is_valid=True if odds in range,
            or is_valid=False with error message if outside range.

        Example:
            >>> pick = Pick(odds=Odds(2.50), ...)
            >>> result = await validator.validate(pick)
            >>> result.is_valid
            True
        """
        if pick.odds.is_in_range(self._min_odds, self._max_odds):
            return ValidationResult(is_valid=True)

        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Odds {pick.odds.value:.2f} outside range "
                f"[{self._min_odds:.2f}, {self._max_odds:.2f}]"
            ),
        )
