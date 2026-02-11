import asyncio
import time
from collections import defaultdict


class AsyncRateLimiter:
    def __init__(self, requests_per_second: float = 2.0):
        self.rps = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._last_request: dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str = "global"):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request[domain]
            if elapsed < self.min_interval:
                wait = self.min_interval - elapsed
                await asyncio.sleep(wait)
            self._last_request[domain] = time.monotonic()
