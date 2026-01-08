"""Shared fixtures for integration tests.

Provides Redis fixtures for integration tests.
Supports two modes:
1. Testcontainers (if Docker is available) - Automatic, isolated
2. Local Redis (docker-compose.dev.yml) - Manual, requires `docker-compose up`

Reference:
- docs/05-Implementation.md: Task 5A.3
"""

from __future__ import annotations

import os

import pytest

from src.infrastructure.repositories.redis_repository import RedisRepository

# Check if we should skip Testcontainers
USE_LOCAL_REDIS = os.environ.get("USE_LOCAL_REDIS", "true").lower() == "true"


@pytest.fixture(scope="module")
def redis_container():
    """Launch Redis container for integration tests.

    If USE_LOCAL_REDIS=true (default), uses localhost:6379.
    Otherwise, tries to use Testcontainers.

    Yields:
        Object with get_container_host_ip() and get_exposed_port() methods.
    """
    if USE_LOCAL_REDIS:
        # Mock container that returns localhost connection
        class LocalRedis:
            def get_container_host_ip(self) -> str:
                return "localhost"

            def get_exposed_port(self, port: int) -> int:
                return port

        yield LocalRedis()
    else:
        # Use Testcontainers
        from testcontainers.redis import RedisContainer

        with RedisContainer("redis:7-alpine") as redis:
            yield redis


@pytest.fixture
async def redis_repo(redis_container):
    """Create RedisRepository connected to test Redis.

    Uses test database (db=15) for isolation from other databases.
    Cleans up data after each test by flushing the database.

    Args:
        redis_container: The Redis container/local fixture.

    Yields:
        RedisRepository: Connected repository instance.
    """
    host = redis_container.get_container_host_ip()
    port = int(redis_container.get_exposed_port(6379))

    repo = RedisRepository(
        host=host,
        port=port,
        db=15,  # Isolated test database
        max_connections=10,
        local_cache_size=100,
    )

    # Initialize connection
    await repo._get_client()

    yield repo

    # Cleanup: flush test database and close
    try:
        client = await repo._get_client()
        await client.flushdb()
    finally:
        await repo.close()

