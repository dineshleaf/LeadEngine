import asyncio
import logging
import random

import httpx

from app.config import settings
from app.utils.rate_limiter import AsyncRateLimiter
from app.utils.url_helpers import extract_domain

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

_rate_limiter = AsyncRateLimiter(settings.requests_per_second)


class Scraper:
    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.request_timeout),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10,
                ),
                verify=False,
            )
        return self.client

    def _random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    async def fetch(
        self,
        url: str,
        max_retries: int = 2,
        follow_redirects: bool = True,
    ) -> httpx.Response | None:
        domain = extract_domain(url)
        await _rate_limiter.acquire(domain)

        client = await self._get_client()
        headers = {
            "User-Agent": self._random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        for attempt in range(max_retries + 1):
            try:
                response = await client.get(
                    url,
                    headers=headers,
                    follow_redirects=follow_redirects,
                )
                return response
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError) as e:
                if attempt < max_retries:
                    wait = (2 ** attempt) + random.random()
                    logger.warning(f"Retry {attempt+1} for {url}: {e}")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries+1} attempts: {e}")
                    return None

    async def fetch_head(self, url: str) -> httpx.Response | None:
        domain = extract_domain(url)
        await _rate_limiter.acquire(domain)

        client = await self._get_client()
        headers = {"User-Agent": self._random_ua()}

        try:
            return await client.head(url, headers=headers, follow_redirects=True)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError) as e:
            logger.warning(f"HEAD request failed for {url}: {e}")
            return None

    async def close(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()


scraper = Scraper()
