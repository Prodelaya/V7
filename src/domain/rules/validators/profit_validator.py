"""Profit validator - OPTIONAL SAFETY CHECK for profit range.

This validator is OPTIONAL since ADR-015 implements origin filtering:
- API parameter `min-profit=-1` already filters minimum profit
- API parameter `max-profit=25` already filters maximum profit

Keep as safety check in case:
- API parameters change or fail silently
- Configuration mismatch between API params and validator

Implementation Requirements:
- Validate profit between MIN_PROFIT (-1%) and MAX_PROFIT (25%)
- CPU-only operation (no I/O) - ~0ms overhead

Note:
    Unlike OddsValidator which receives Pick, ProfitValidator receives Surebet
    because profit is an attribute of Surebet, not Pick. This is a deliberate
    design decision documented in Task 3.3.

Reference:
- docs/03-ADRs.md: ADR-015 (Origin Filtering)
- docs/05-Implementation.md: Task 3.3
- docs/01-SRS.md: RF-003 (validation requirements)
"""

from src.domain.entities.surebet import Surebet

from .base import BaseValidator, ValidationResult


class ProfitValidator(BaseValidator):
    """OPTIONAL SAFETY CHECK: Validator for surebet profit range.

    Since ADR-015, the API filters profit at origin with min-profit/max-profit.
    This validator serves as a redundant safety check (~0ms overhead).

    Can be disabled in validation chain if full trust in API is desired.

    Checks that profit is within configured range:
    - Minimum: -1% (default, from SRS)
    - Maximum: 25% (default, from SRS)

    Note:
        Receives Surebet (not Pick) because profit is a Surebet attribute.

    Example:
        >>> validator = ProfitValidator(min_profit=-1.0, max_profit=25.0)
        >>> result = await validator.validate(surebet)
        >>> result.is_valid
        True

    Reference:
        - ADR-015 in docs/03-ADRs.md (Origin Filtering)
        - Task 3.3 in docs/05-Implementation.md
        - RF-003 in docs/01-SRS.md
    """

    def __init__(self, min_profit: float = -1.0, max_profit: float = 25.0):
        """Initialize with profit range.

        Args:
            min_profit: Minimum acceptable profit percent (default -1%)
            max_profit: Maximum acceptable profit percent (default 25%)

        Raises:
            ValueError: If min_profit >= max_profit
        """
        if min_profit >= max_profit:
            raise ValueError(
                f"min_profit ({min_profit}) must be less than max_profit ({max_profit})"
            )
        self._min_profit = min_profit
        self._max_profit = max_profit

    @property
    def name(self) -> str:
        """Return validator identifier."""
        return "ProfitValidator"

    async def validate(self, surebet: Surebet) -> ValidationResult:
        """Check if surebet profit is within configured range.

        Uses the Profit value object's is_acceptable() method for validation.
        This is a CPU-only operation with ~0ms overhead.

        Args:
            surebet: Surebet entity to validate (contains profit)

        Returns:
            ValidationResult with is_valid=True if profit in range,
            or is_valid=False with error message if outside range.

        Example:
            >>> surebet = Surebet(..., profit=Profit(2.5))
            >>> result = await validator.validate(surebet)
            >>> result.is_valid
            True
        """
        if surebet.profit.is_acceptable(self._min_profit, self._max_profit):
            return ValidationResult(is_valid=True)

        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Profit {surebet.profit.value:.2f}% outside range "
                f"[{self._min_profit:.2f}%, {self._max_profit:.2f}%]"
            ),
        )
