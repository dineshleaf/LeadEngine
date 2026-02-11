import re

from bs4 import BeautifulSoup

from app.analyzers.base import BaseAnalyzer
from app.services.scraper import scraper
from app.utils.patterns import (
    CONTACT_PAGE_PATHS,
    EMAIL_BLACKLIST_PATTERNS,
    EMAIL_REGEX,
    PHONE_REGEX_INTL,
    PHONE_REGEX_US,
)
from app.utils.url_helpers import get_base_url


class ContactInfoAnalyzer(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        contacts = []
        seen_values = set()

        # First check homepage
        response = await scraper.fetch(base_url)
        if response and response.status_code == 200:
            found = self._extract_contacts(response.text, base_url, domain)
            for c in found:
                if c["value"] not in seen_values:
                    seen_values.add(c["value"])
                    contacts.append(c)

        # Then check contact/about pages
        for path in CONTACT_PAGE_PATHS:
            url = f"{base_url}{path}"
            response = await scraper.fetch(url)
            if response and response.status_code == 200:
                found = self._extract_contacts(response.text, url, domain)
                for c in found:
                    if c["value"] not in seen_values:
                        seen_values.add(c["value"])
                        contacts.append(c)
                if contacts:
                    break

        return {"contacts": contacts[:20]}

    def _extract_contacts(self, html: str, page_url: str, domain: str) -> list[dict]:
        contacts = []
        soup = BeautifulSoup(html, "lxml")

        # Extract emails from mailto links (highest confidence)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("mailto:"):
                email = href[7:].split("?")[0].strip()
                if self._is_valid_email(email, domain):
                    contacts.append({
                        "type": "email",
                        "value": email,
                        "source": "mailto_link",
                        "page_url": page_url,
                        "confidence": 1.0,
                    })

        # Extract emails from visible text
        text = soup.get_text(" ", strip=True)
        email_matches = re.findall(EMAIL_REGEX, text)
        for email in email_matches:
            if self._is_valid_email(email, domain):
                contacts.append({
                    "type": "email",
                    "value": email.lower(),
                    "source": "page_text",
                    "page_url": page_url,
                    "confidence": 0.8,
                })

        # Extract phones from tel: links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("tel:"):
                phone = href[4:].strip()
                if len(phone) >= 7:
                    contacts.append({
                        "type": "phone",
                        "value": phone,
                        "source": "tel_link",
                        "page_url": page_url,
                        "confidence": 1.0,
                    })

        # Extract phones from visible text
        phone_matches_us = re.findall(PHONE_REGEX_US, text)
        phone_matches_intl = re.findall(PHONE_REGEX_INTL, text)
        all_phones = set(phone_matches_us + phone_matches_intl)

        for phone in all_phones:
            cleaned = re.sub(r"[^\d+]", "", phone)
            if len(cleaned) >= 7:
                contacts.append({
                    "type": "phone",
                    "value": phone.strip(),
                    "source": "page_text",
                    "page_url": page_url,
                    "confidence": 0.7,
                })

        # Deduplicate within this page
        seen = set()
        unique = []
        for c in contacts:
            key = (c["type"], c["value"].lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    def _is_valid_email(self, email: str, domain: str) -> bool:
        email = email.lower().strip()
        if not re.match(EMAIL_REGEX, email):
            return False
        for blacklist_pattern in EMAIL_BLACKLIST_PATTERNS:
            if re.match(blacklist_pattern, email, re.IGNORECASE):
                return False
        # Prefer emails from the same domain, but accept others too
        return True
