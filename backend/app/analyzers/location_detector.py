import json
import re

from bs4 import BeautifulSoup

from app.analyzers.base import BaseAnalyzer
from app.services.scraper import scraper
from app.utils.url_helpers import get_base_url


# Common country phone prefixes for guessing country from phone numbers
PHONE_COUNTRY_MAP = {
    "+1": "United States", "+44": "United Kingdom", "+61": "Australia",
    "+91": "India", "+49": "Germany", "+33": "France", "+39": "Italy",
    "+34": "Spain", "+31": "Netherlands", "+46": "Sweden", "+47": "Norway",
    "+45": "Denmark", "+358": "Finland", "+64": "New Zealand", "+27": "South Africa",
    "+55": "Brazil", "+52": "Mexico", "+81": "Japan", "+82": "South Korea",
    "+86": "China", "+971": "UAE", "+966": "Saudi Arabia", "+65": "Singapore",
    "+60": "Malaysia", "+62": "Indonesia", "+63": "Philippines", "+66": "Thailand",
}


class LocationDetector(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        location = {"country": None, "state": None, "city": None, "address": None}

        response = await scraper.fetch(base_url)
        if not response or response.status_code >= 400:
            return location

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # 1. Schema.org structured data (most reliable)
        schema_loc = self._extract_schema_location(html)
        if schema_loc.get("country"):
            return schema_loc

        # 2. Meta geo tags
        meta_loc = self._extract_meta_geo(soup)
        if meta_loc.get("country"):
            return meta_loc

        # 3. Footer / address tags
        address_loc = self._extract_address_from_html(soup)
        if address_loc.get("country") or address_loc.get("city"):
            return address_loc

        # 4. Try contact page
        for path in ["/contact", "/contact-us", "/about"]:
            resp = await scraper.fetch(f"{base_url}{path}")
            if resp and resp.status_code == 200:
                contact_soup = BeautifulSoup(resp.text, "lxml")
                schema_loc = self._extract_schema_location(resp.text)
                if schema_loc.get("country"):
                    return schema_loc
                address_loc = self._extract_address_from_html(contact_soup)
                if address_loc.get("country") or address_loc.get("city"):
                    return address_loc

        # 5. Guess from phone numbers on page
        phone_loc = self._guess_country_from_phone(soup.get_text())
        if phone_loc:
            location["country"] = phone_loc

        return location

    def _extract_schema_location(self, html: str) -> dict:
        location = {"country": None, "state": None, "city": None, "address": None}
        try:
            ld_blocks = re.findall(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html, re.DOTALL | re.IGNORECASE,
            )
            for block in ld_blocks:
                try:
                    data = json.loads(block)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        addr = item.get("address")
                        if not addr and item.get("location"):
                            loc = item["location"]
                            addr = loc.get("address") if isinstance(loc, dict) else None
                        if isinstance(addr, dict):
                            location["country"] = addr.get("addressCountry")
                            location["state"] = addr.get("addressRegion")
                            location["city"] = addr.get("addressLocality")
                            street = addr.get("streetAddress", "")
                            postal = addr.get("postalCode", "")
                            parts = [p for p in [street, location["city"], location["state"], postal, location["country"]] if p]
                            location["address"] = ", ".join(parts) if parts else None
                            if location["country"]:
                                return location
                        elif isinstance(addr, str) and len(addr) > 5:
                            location["address"] = addr
                except (json.JSONDecodeError, AttributeError):
                    pass
        except Exception:
            pass
        return location

    def _extract_meta_geo(self, soup: BeautifulSoup) -> dict:
        location = {"country": None, "state": None, "city": None, "address": None}
        region = soup.find("meta", attrs={"name": "geo.region"})
        if region:
            content = region.get("content", "")
            parts = content.split("-")
            if len(parts) >= 1:
                location["country"] = parts[0]
            if len(parts) >= 2:
                location["state"] = parts[1]

        placename = soup.find("meta", attrs={"name": "geo.placename"})
        if placename:
            location["city"] = placename.get("content")

        return location

    def _extract_address_from_html(self, soup: BeautifulSoup) -> dict:
        location = {"country": None, "state": None, "city": None, "address": None}

        # Check <address> tags
        address_tags = soup.find_all("address")
        for tag in address_tags:
            text = tag.get_text(" ", strip=True)
            if len(text) > 10:
                location["address"] = text[:200]
                country = self._guess_country_from_text(text)
                if country:
                    location["country"] = country
                return location

        # Check footer for address-like content
        footer = soup.find("footer")
        if footer:
            text = footer.get_text(" ", strip=True)
            country = self._guess_country_from_text(text)
            if country:
                location["country"] = country

        return location

    def _guess_country_from_text(self, text: str) -> str | None:
        countries = {
            "United States": ["united states", "usa", ", us", " us ", "u.s.a"],
            "United Kingdom": ["united kingdom", ", uk", " uk ", "england", "london"],
            "Australia": ["australia", "sydney", "melbourne"],
            "Canada": ["canada", "toronto", "vancouver"],
            "Germany": ["germany", "deutschland", "berlin", "munich"],
            "France": ["france", "paris"],
            "India": ["india", "mumbai", "delhi", "bangalore"],
            "Netherlands": ["netherlands", "amsterdam"],
            "Spain": ["spain", "madrid", "barcelona"],
            "Italy": ["italy", "milan", "rome"],
            "UAE": ["dubai", "abu dhabi", "united arab emirates"],
            "Singapore": ["singapore"],
            "New Zealand": ["new zealand", "auckland"],
            "Ireland": ["ireland", "dublin"],
            "Sweden": ["sweden", "stockholm"],
        }
        text_lower = text.lower()
        for country, keywords in countries.items():
            for kw in keywords:
                if kw in text_lower:
                    return country
        return None

    def _guess_country_from_phone(self, text: str) -> str | None:
        phones = re.findall(r"\+\d{1,3}", text)
        for phone in phones:
            for prefix, country in PHONE_COUNTRY_MAP.items():
                if phone.startswith(prefix):
                    return country
        return None
