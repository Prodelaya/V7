"""Custom exception classes for Retador v2.0.

Hierarchy (PDR Section 7.1):
    RetadorError (base)
    ├── DomainError
    │   ├── InvalidOddsError
    │   ├── InvalidProfitError
    │   └── InvalidMarketError
    ├── InfrastructureError
    │   ├── ApiError (alias: ApiConnectionError)
    │   ├── ApiRateLimitError
    │   ├── RedisError (alias: RedisConnectionError)
    │   └── TelegramError (alias: TelegramSendError)
    └── ApplicationError
        ├── ValidationError
        └── ProcessingError

Reference:
- docs/02-PDR.md: Section 7.1
- docs/05-Implementation.md: Task 1.1
"""

from __future__ import annotations

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASE EXCEPTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class RetadorError(Exception):
    """Base exception for all Retador application errors."""

    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DOMAIN ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class DomainError(RetadorError):
    """Base exception for business logic errors.

    Use for errors in domain layer (value objects, entities, domain services).
    Strategy: Log and discard the pick.
    """

    pass


class InvalidOddsError(DomainError):
    """Raised when odds are outside valid range [1.01, 1000].

    Examples:
        >>> raise InvalidOddsError("Odds 0.99 below minimum 1.01")
        >>> raise InvalidOddsError("Odds 1001 above maximum 1000")
    """

    pass


class InvalidProfitError(DomainError):
    """Raised when profit is outside valid range [-100, 100].

    Examples:
        >>> raise InvalidProfitError("Profit 150% exceeds maximum 100%")
    """

    pass


class InvalidMarketError(DomainError):
    """Raised when market type is invalid or unrecognized.

    Examples:
        >>> raise InvalidMarketError("Unknown market type: 'xyz'")
    """

    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INFRASTRUCTURE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class InfrastructureError(RetadorError):
    """Base exception for external service errors.

    Use for errors in infrastructure layer (API, Redis, Telegram).
    Strategy: Retry with exponential backoff.
    """

    pass


class ApiError(InfrastructureError):
    """Raised when API request fails.

    Attributes:
        status_code: HTTP status code from the API response.

    Examples:
        >>> raise ApiError("Connection timeout", status_code=0)
        >>> raise ApiError("Server error", status_code=500)
    """

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class ApiRateLimitError(InfrastructureError):
    """Raised when API rate limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header).

    Examples:
        >>> raise ApiRateLimitError("Rate limit exceeded", retry_after=60)
    """

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class RedisError(InfrastructureError):
    """Raised when Redis operation fails.

    Examples:
        >>> raise RedisError("Connection refused")
        >>> raise RedisError("Key not found")
    """

    pass


class TelegramError(InfrastructureError):
    """Raised when Telegram operation fails.

    Examples:
        >>> raise TelegramError("Bot blocked by user")
        >>> raise TelegramError("Chat not found")
    """

    pass


# Backward compatibility aliases (PDR uses both naming conventions)
ApiConnectionError = ApiError
RedisConnectionError = RedisError
TelegramSendError = TelegramError


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLICATION ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ApplicationError(RetadorError):
    """Base exception for orchestration errors.

    Use for errors in application layer (handlers, DTOs).
    Strategy: Log and continue processing.
    """

    pass


class ValidationError(ApplicationError):
    """Raised when pick validation fails.

    Attributes:
        validator: Name of the validator that failed.

    Examples:
        >>> raise ValidationError("Odds out of range", validator="OddsValidator")
    """

    def __init__(self, message: str, validator: str = ""):
        super().__init__(message)
        self.validator = validator


class ProcessingError(ApplicationError):
    """Raised when pick processing fails.

    Attributes:
        pick_id: Identifier of the pick that failed processing.

    Examples:
        >>> raise ProcessingError("Failed to format message", pick_id="abc123")
    """

    def __init__(self, message: str, pick_id: str | None = None):
        super().__init__(message)
        self.pick_id = pick_id
