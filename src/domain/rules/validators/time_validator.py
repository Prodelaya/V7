"""Time validator - REQUIRED: Check if event is in the future.

IMPORTANT: This validator is NOT redundant with API's startAge parameter!
- startAge=PT10M filters surebet CREATION time (when record was created)
- TimeValidator checks EVENT START time (when the match begins)

These are different things:
- A surebet created 1 minute ago (passes startAge) could be for a match
  that started 10 minutes ago (fails TimeValidator)

Implementation Requirements:
- Validate event time is in the future (>0 seconds from now)
- Support configurable min_seconds buffer for safety margin
- CPU-only operation (no I/O) - ~0ms overhead

Reference:
- docs/03-ADRs.md: ADR-015 (explains difference from startAge)
- docs/05-Implementation.md: Task 3.4
- docs/01-SRS.md: RF-003 (validation requirements)
"""

from src.domain.entities.pick import Pick

from .base import BaseValidator, ValidationResult


class TimeValidator(BaseValidator):
    """REQUIRED: Validator for event timing.

    Unlike OddsValidator/ProfitValidator, this is NOT optional because:
    - API's startAge filters surebet CREATION time
    - This validator checks EVENT START time

    A surebet can be "fresh" (created recently) but for an event
    that has already started. This validator catches those.

    Checks that event starts in the future with configurable buffer.

    Example:
        >>> validator = TimeValidator(min_seconds=0)
        >>> result = await validator.validate(pick)
        >>> result.is_valid
        True

    Reference:
        - ADR-015 in docs/03-ADRs.md
        - Task 3.4 in docs/05-Implementation.md
        - RF-003 in docs/01-SRS.md
    """

    def __init__(self, min_seconds: float = 0.0):
        """Initialize with minimum time buffer.

        Args:
            min_seconds: Minimum seconds until event start (default 0).
                        Use positive values for safety buffer.
                        Example: min_seconds=60 requires 1 minute before event.

        Raises:
            ValueError: If min_seconds is negative.
        """
        if min_seconds < 0:
            raise ValueError(
                f"min_seconds ({min_seconds}) cannot be negative"
            )
        self._min_seconds = min_seconds

    @property
    def name(self) -> str:
        """Return validator identifier."""
        return "TimeValidator"

    async def validate(self, pick: Pick) -> ValidationResult:
        """Check if event starts in the future with required buffer.

        Verifies that the event has not started yet and that there's
        sufficient time buffer as configured by min_seconds.

        This is a CPU-only operation with ~0ms overhead.

        Args:
            pick: Pick entity to validate

        Returns:
            ValidationResult with is_valid=True if event is in future
            with sufficient buffer, or is_valid=False with descriptive
            error message if event started or starts too soon.

        Example:
            >>> pick = Pick(..., event_time=future_datetime, ...)
            >>> result = await validator.validate(pick)
            >>> result.is_valid
            True
        """
        seconds_until = pick.seconds_until_event()

        if seconds_until > self._min_seconds:
            return ValidationResult(is_valid=True)

        # Generate appropriate error message based on scenario
        if seconds_until <= 0:
            elapsed = abs(seconds_until)
            return ValidationResult(
                is_valid=False,
                error_message=f"Event started {elapsed:.0f} seconds ago",
            )
        else:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"Event starts in {seconds_until:.0f}s, "
                    f"minimum required is {self._min_seconds:.0f}s"
                ),
            )
