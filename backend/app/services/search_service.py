import asyncio
import logging
from typing import Optional

from app.utils.url_helpers import extract_domain

logger = logging.getLogger(__name__)


async def search_google(query: str, max_results: int = 20) -> list[dict]:
    """Search Google for domains. Uses googlesearch-python library."""
    try:
        from googlesearch import search as gsearch

        results = []
        seen_domains = set()

        def _do_search():
            found = []
            for result in gsearch(query, num_results=max_results, lang="en"):
                found.append(result)
            return found

        urls = await asyncio.to_thread(_do_search)

        for url in urls:
            domain = extract_domain(url)
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                results.append({
                    "domain": domain,
                    "url": url,
                    "title": domain,
                    "snippet": "",
                })

        return results[:max_results]
    except ImportError:
        logger.warning("googlesearch-python not installed. Discovery feature disabled.")
        return []
    except Exception as e:
        logger.error(f"Google search failed: {e}")
        return []
