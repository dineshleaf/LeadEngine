import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.analyzers.base import BaseAnalyzer
from app.services.scraper import scraper
from app.utils.patterns import SOCIAL_DOMAIN_MAP, SOCIAL_URL_PATTERNS
from app.utils.url_helpers import get_base_url


class SocialMediaAnalyzer(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        response = await scraper.fetch(base_url)

        profiles: dict[str, str | None] = {
            "instagram": None,
            "facebook": None,
            "tiktok": None,
            "twitter": None,
            "linkedin": None,
            "youtube": None,
        }
        activity: dict[str, bool | None] = {k: None for k in profiles}

        if not response or response.status_code >= 400:
            return self._build_result(profiles, activity)

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # Extract all links
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith(("http://", "https://")):
                links.add(href)

        # Match links to social platforms
        for link in links:
            try:
                parsed = urlparse(link)
                host = parsed.netloc.lower().replace("www.", "")
                for domain_pattern, platform in SOCIAL_DOMAIN_MAP.items():
                    if domain_pattern in host and profiles[platform] is None:
                        # Validate it's not just a share/intent link
                        path = parsed.path.strip("/")
                        if path and not self._is_share_link(link, platform):
                            profiles[platform] = link
            except Exception:
                continue

        # Verify profiles exist and check activity
        for platform, url in profiles.items():
            if url:
                is_active = await self._check_profile(url, platform)
                activity[platform] = is_active

        return self._build_result(profiles, activity)

    def _is_share_link(self, url: str, platform: str) -> bool:
        share_indicators = [
            "sharer", "share", "intent/tweet", "pin/create",
            "/dialog/", "redirect", "/plugins/",
        ]
        url_lower = url.lower()
        return any(ind in url_lower for ind in share_indicators)

    async def _check_profile(self, url: str, platform: str) -> bool | None:
        """Check if a social profile exists and is active."""
        try:
            response = await scraper.fetch_head(url)
            if response and response.status_code == 200:
                return True
            elif response and response.status_code == 404:
                return False
            return None
        except Exception:
            return None

    def _build_result(
        self,
        profiles: dict[str, str | None],
        activity: dict[str, bool | None],
    ) -> dict:
        activity_details = {}
        for platform in profiles:
            if profiles[platform]:
                activity_details[platform] = {
                    "url": profiles[platform],
                    "active": activity.get(platform),
                }

        return {
            "instagram_url": profiles.get("instagram"),
            "facebook_url": profiles.get("facebook"),
            "tiktok_url": profiles.get("tiktok"),
            "twitter_url": profiles.get("twitter"),
            "linkedin_url": profiles.get("linkedin"),
            "youtube_url": profiles.get("youtube"),
            "instagram_active": activity.get("instagram"),
            "facebook_active": activity.get("facebook"),
            "tiktok_active": activity.get("tiktok"),
            "twitter_active": activity.get("twitter"),
            "linkedin_active": activity.get("linkedin"),
            "activity_details": activity_details,
        }
