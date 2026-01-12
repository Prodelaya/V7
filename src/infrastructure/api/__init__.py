"""API package - External API integrations.

Contains:
- surebet_client: Client for apostasseguras.com API
- rate_limiter: Adaptive rate limiting with backoff
- prefetch_manager: Parallel prefetching for reduced latency

Reference: docs/05-Implementation.md Phase 5
"""

from .prefetch_manager import PrefetchManager
from .rate_limiter import AdaptiveRateLimiter
from .surebet_client import SurebetClient

__all__ = ["SurebetClient", "AdaptiveRateLimiter", "PrefetchManager"]
