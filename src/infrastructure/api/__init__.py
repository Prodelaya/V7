"""API package - External API integrations.

Contains:
- surebet_client: Client for apostasseguras.com API
- rate_limiter: Adaptive rate limiting with backoff

Reference: docs/05-Implementation.md Phase 5
"""

from .surebet_client import SurebetClient
from .rate_limiter import AdaptiveRateLimiter

__all__ = ["SurebetClient", "AdaptiveRateLimiter"]
