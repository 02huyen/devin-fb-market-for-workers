"""In-memory sliding-window rate limiter.

Simple, dependency-free rate limiting for a single process. For a multi-worker
or multi-node deployment the window state should be moved to Redis / memcached.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List


class SlidingWindowRateLimiter:
    """Sliding-window counter per key."""

    def __init__(self):
        self._windows: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, limit: int, window_seconds: float) -> bool:
        """Return True if the action is within the limit.

        Each key tracks monotonic timestamps. Old timestamps outside the window
        are removed before counting.
        """
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            timestamps = self._windows[key]
            # Timestamps are appended in chronological order, so the first one
            # is always the oldest.
            while timestamps and timestamps[0] <= cutoff:
                timestamps.pop(0)
            if len(timestamps) >= limit:
                return False
            timestamps.append(now)
            return True


rate_limiter = SlidingWindowRateLimiter()
