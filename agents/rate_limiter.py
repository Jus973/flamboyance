"""Global rate limiter for LLM API requests.

Implements a singleton pattern to enforce rate limiting across all LLMDriver
instances, preventing concurrent requests from exceeding API rate limits.
"""

from __future__ import annotations

import asyncio
import logging
import time

log = logging.getLogger(__name__)


class GlobalRateLimiter:
    """Singleton rate limiter that enforces minimum delays between API requests.

    Uses class variables to maintain state across all instances, ensuring that
    rate limiting is applied globally regardless of how many LLMDriver instances
    exist.
    """

    _lock: asyncio.Lock | None = None
    _last_request_time: float = 0.0

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the async lock (must be called from async context)."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    async def acquire(cls, min_delay: float) -> None:
        """Acquire permission to make an API request.

        Blocks until enough time has passed since the last request to satisfy
        the minimum delay requirement.

        Args:
            min_delay: Minimum seconds that must elapse between requests.
        """
        async with cls._get_lock():
            now = time.monotonic()
            time_since_last = now - cls._last_request_time
            wait_time = max(0.0, min_delay - time_since_last)

            if wait_time > 0:
                log.debug(
                    "Global rate limiter: waiting %.2fs before next request",
                    wait_time,
                )
                await asyncio.sleep(wait_time)

            cls._last_request_time = time.monotonic()

    @classmethod
    def reset(cls) -> None:
        """Reset the rate limiter state (useful for testing)."""
        cls._last_request_time = 0.0
        cls._lock = None
