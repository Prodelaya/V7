"""Tests for exception hierarchy.

Verifies:
- Correct inheritance hierarchy per PDR Section 7.1
- Exception attributes (status_code, validator, etc.)
- Backward compatibility aliases

Reference: docs/02-PDR.md Section 7.1
"""

import pytest

from src.shared.exceptions import (
    ApiConnectionError,
    ApiError,
    ApiRateLimitError,
    # Application
    ApplicationError,
    # Domain
    DomainError,
    # Infrastructure
    InfrastructureError,
    InvalidMarketError,
    InvalidOddsError,
    InvalidProfitError,
    ProcessingError,
    RedisConnectionError,
    RedisError,
    # Base
    RetadorError,
    TelegramError,
    TelegramSendError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_retador_error_is_base_exception(self):
        """RetadorError should inherit from Exception."""
        assert issubclass(RetadorError, Exception)

    def test_domain_error_inherits_from_retador_error(self):
        """DomainError should inherit from RetadorError."""
        assert issubclass(DomainError, RetadorError)

    def test_infrastructure_error_inherits_from_retador_error(self):
        """InfrastructureError should inherit from RetadorError."""
        assert issubclass(InfrastructureError, RetadorError)

    def test_application_error_inherits_from_retador_error(self):
        """ApplicationError should inherit from RetadorError."""
        assert issubclass(ApplicationError, RetadorError)


class TestDomainErrors:
    """Tests for domain-specific exceptions."""

    def test_invalid_odds_is_domain_error(self):
        """InvalidOddsError should inherit from DomainError."""
        assert issubclass(InvalidOddsError, DomainError)
        error = InvalidOddsError("Odds out of range")
        assert isinstance(error, DomainError)
        assert isinstance(error, RetadorError)

    def test_invalid_profit_is_domain_error(self):
        """InvalidProfitError should inherit from DomainError."""
        assert issubclass(InvalidProfitError, DomainError)
        error = InvalidProfitError("Profit out of range")
        assert isinstance(error, DomainError)

    def test_invalid_market_is_domain_error(self):
        """InvalidMarketError should inherit from DomainError."""
        assert issubclass(InvalidMarketError, DomainError)
        error = InvalidMarketError("Unknown market")
        assert isinstance(error, DomainError)


class TestInfrastructureErrors:
    """Tests for infrastructure-specific exceptions."""

    def test_api_error_is_infrastructure_error(self):
        """ApiError should inherit from InfrastructureError."""
        assert issubclass(ApiError, InfrastructureError)
        error = ApiError("Connection failed")
        assert isinstance(error, InfrastructureError)

    def test_api_error_has_status_code(self):
        """ApiError should have status_code attribute."""
        error = ApiError("Server error", status_code=500)
        assert error.status_code == 500

    def test_api_error_default_status_code(self):
        """ApiError should default status_code to 0."""
        error = ApiError("Connection timeout")
        assert error.status_code == 0

    def test_api_rate_limit_error_is_infrastructure_error(self):
        """ApiRateLimitError should inherit from InfrastructureError."""
        assert issubclass(ApiRateLimitError, InfrastructureError)

    def test_api_rate_limit_has_retry_after(self):
        """ApiRateLimitError should have retry_after attribute."""
        error = ApiRateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60

    def test_api_rate_limit_default_retry_after(self):
        """ApiRateLimitError should default retry_after to None."""
        error = ApiRateLimitError("Rate limited")
        assert error.retry_after is None

    def test_redis_error_is_infrastructure_error(self):
        """RedisError should inherit from InfrastructureError."""
        assert issubclass(RedisError, InfrastructureError)

    def test_telegram_error_is_infrastructure_error(self):
        """TelegramError should inherit from InfrastructureError."""
        assert issubclass(TelegramError, InfrastructureError)


class TestApplicationErrors:
    """Tests for application-specific exceptions."""

    def test_validation_error_is_application_error(self):
        """ValidationError should inherit from ApplicationError."""
        assert issubclass(ValidationError, ApplicationError)

    def test_validation_error_has_validator(self):
        """ValidationError should have validator attribute."""
        error = ValidationError("Invalid odds", validator="OddsValidator")
        assert error.validator == "OddsValidator"

    def test_validation_error_default_validator(self):
        """ValidationError should default validator to empty string."""
        error = ValidationError("Invalid")
        assert error.validator == ""

    def test_processing_error_is_application_error(self):
        """ProcessingError should inherit from ApplicationError."""
        assert issubclass(ProcessingError, ApplicationError)

    def test_processing_error_has_pick_id(self):
        """ProcessingError should have pick_id attribute."""
        error = ProcessingError("Processing failed", pick_id="abc123")
        assert error.pick_id == "abc123"

    def test_processing_error_default_pick_id(self):
        """ProcessingError should default pick_id to None."""
        error = ProcessingError("Processing failed")
        assert error.pick_id is None


class TestBackwardCompatibilityAliases:
    """Tests for backward compatibility aliases."""

    def test_api_connection_error_is_api_error(self):
        """ApiConnectionError should be alias for ApiError."""
        assert ApiConnectionError is ApiError

    def test_redis_connection_error_is_redis_error(self):
        """RedisConnectionError should be alias for RedisError."""
        assert RedisConnectionError is RedisError

    def test_telegram_send_error_is_telegram_error(self):
        """TelegramSendError should be alias for TelegramError."""
        assert TelegramSendError is TelegramError


class TestExceptionMessages:
    """Tests for exception message handling."""

    def test_exception_message_preserved(self):
        """Exception message should be preserved in str()."""
        msg = "This is the error message"
        error = RetadorError(msg)
        assert str(error) == msg

    def test_domain_error_message_preserved(self):
        """DomainError message should be preserved."""
        msg = "Invalid odds value"
        error = InvalidOddsError(msg)
        assert str(error) == msg

    def test_can_catch_all_domain_errors(self):
        """Should be able to catch all domain errors with DomainError."""
        errors = [
            InvalidOddsError("test"),
            InvalidProfitError("test"),
            InvalidMarketError("test"),
        ]
        for error in errors:
            try:
                raise error
            except DomainError:
                pass  # Expected
            except Exception:
                pytest.fail(f"{type(error).__name__} not caught by DomainError")

    def test_can_catch_all_infrastructure_errors(self):
        """Should be able to catch all infra errors with InfrastructureError."""
        errors = [
            ApiError("test"),
            ApiRateLimitError("test"),
            RedisError("test"),
            TelegramError("test"),
        ]
        for error in errors:
            try:
                raise error
            except InfrastructureError:
                pass  # Expected
            except Exception:
                pytest.fail(
                    f"{type(error).__name__} not caught by InfrastructureError"
                )

    def test_can_catch_all_retador_errors(self):
        """Should be able to catch all errors with RetadorError."""
        errors = [
            InvalidOddsError("test"),
            ApiError("test"),
            ValidationError("test"),
        ]
        for error in errors:
            try:
                raise error
            except RetadorError:
                pass  # Expected
            except Exception:
                pytest.fail(f"{type(error).__name__} not caught by RetadorError")
