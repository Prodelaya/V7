"""Repositories package - Data persistence.

Contains:
- base: Abstract repository interface
- redis_repository: Redis for deduplication (NO Bloom Filter)
- _postgres_repository: Future PostgreSQL for history

Reference: docs/05-Implementation.md Phase 5
"""

from .base import BaseRepository
from .redis_repository import RedisRepository

__all__ = ["BaseRepository", "RedisRepository"]
