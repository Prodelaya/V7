"""Custom exception classes.

Implementation Requirements:
- Base RetadorError class
- Domain-specific exceptions (odds, profit, validation)
- Infrastructure exceptions (API, Redis)

Reference:
- docs/05-Implementation.md: Task 1.1

TODO: Implement exception classes
"""


class RetadorError(Exception):
    """Base exception for Retador application."""
    pass


class InvalidOddsError(RetadorError):
    """Raised when odds are outside valid range."""
    pass


class InvalidProfitError(RetadorError):
    """Raised when profit is outside valid range."""
    pass


class ValidationError(RetadorError):
    """Raised when pick validation fails."""
    
    def __init__(self, message: str, validator: str = ""):
        super().__init__(message)
        self.validator = validator


class ApiError(RetadorError):
    """Raised when API request fails."""
    
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class RedisError(RetadorError):
    """Raised when Redis operation fails."""
    pass


class TelegramError(RetadorError):
    """Raised when Telegram operation fails."""
    pass
