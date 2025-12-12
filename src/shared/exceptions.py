"""Custom exceptions for the Retador system."""


class RetadorError(Exception):
    """Base exception for all Retador errors."""
    pass


class ValidationError(RetadorError):
    """Raised when pick validation fails."""
    
    def __init__(self, message: str, validator: str = None):
        super().__init__(message)
        self.validator = validator


class APIError(RetadorError):
    """Raised when API request fails."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 0):
        super().__init__(f"Rate limit exceeded, retry after {retry_after}s")
        self.retry_after = retry_after


class DuplicatePickError(RetadorError):
    """Raised when a duplicate pick is detected."""
    
    def __init__(self, key: str):
        super().__init__(f"Duplicate pick: {key}")
        self.key = key


class ConnectionError(RetadorError):
    """Raised when connection to external service fails."""
    pass


class ConfigurationError(RetadorError):
    """Raised when configuration is invalid."""
    pass
