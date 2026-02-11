import re

from bs4 import BeautifulSoup

from app.analyzers.base import BaseAnalyzer
from app.services.scraper import scraper
from app.utils.patterns import GOOGLE_ADS_PATTERNS, META_ADS_PATTERNS, TIKTOK_ADS_PATTERNS
from app.utils.url_helpers import get_base_url


class AdActivityAnalyzer(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        response = await scraper.fetch(base_url)

        if not response or response.status_code >= 400:
            return self._empty_result()

        html = response.text

        # Detect ad pixels / conversion scripts in page HTML
        google_ads = self._detect_patterns(html, GOOGLE_ADS_PATTERNS)
        meta_ads = self._detect_patterns(html, META_ADS_PATTERNS)
        tiktok_ads = self._detect_patterns(html, TIKTOK_ADS_PATTERNS)

        # Check Google Ads Transparency Center (public page)
        google_transparency = await self._check_google_ads_transparency(domain)

        # Combine results
        is_google = google_ads["found"] or google_transparency.get("has_ads", False)
        is_meta = meta_ads["found"]
        is_tiktok = tiktok_ads["found"]

        ad_details = {}
        if google_ads["matches"]:
            ad_details["google_pixel_evidence"] = google_ads["matches"]
        if meta_ads["matches"]:
            ad_details["meta_pixel_evidence"] = meta_ads["matches"]
        if tiktok_ads["matches"]:
            ad_details["tiktok_pixel_evidence"] = tiktok_ads["matches"]
        if google_transparency.get("has_ads"):
            ad_details["google_transparency"] = True

        return {
            "is_running_google_ads": is_google,
            "google_ads_count": google_transparency.get("ad_count", 0),
            "google_advertiser_id": google_transparency.get("advertiser_id"),
            "is_running_meta_ads": is_meta,
            "meta_ads_count": 0,
            "meta_page_id": None,
            "is_running_tiktok_ads": is_tiktok,
            "tiktok_ads_count": 0,
            "ad_details": ad_details,
        }

    def _detect_patterns(self, html: str, patterns: list[str]) -> dict:
        matches = []
        for pattern in patterns:
            if re.search(pattern, html, re.IGNORECASE):
                matches.append(pattern)
        return {"found": len(matches) > 0, "matches": matches}

    async def _check_google_ads_transparency(self, domain: str) -> dict:
        """Check if the domain has ads in Google Ads Transparency Center."""
        try:
            url = f"https://adstransparency.google.com/?domain={domain}"
            response = await scraper.fetch(url)
            if response and response.status_code == 200:
                # The transparency center is a JS app, so we can only do a basic check
                # A more complete solution would use a headless browser
                if domain.lower() in response.text.lower():
                    return {"has_ads": True, "ad_count": 0, "advertiser_id": None}
        except Exception as e:
            self.logger.debug(f"Google Ads Transparency check failed for {domain}: {e}")
        return {"has_ads": False, "ad_count": 0, "advertiser_id": None}

    def _empty_result(self) -> dict:
        return {
            "is_running_google_ads": False,
            "google_ads_count": 0,
            "google_advertiser_id": None,
            "is_running_meta_ads": False,
            "meta_ads_count": 0,
            "meta_page_id": None,
            "is_running_tiktok_ads": False,
            "tiktok_ads_count": 0,
            "ad_details": {},
        }
