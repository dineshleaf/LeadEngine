import json
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
    SOCIAL_DOMAIN_MAP,
)
from app.utils.url_helpers import get_base_url


class ContactInfoAnalyzer(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        contacts = []
        seen_values = set()

        def _add_unique(found: list[dict]):
            for c in found:
                key = c["value"].lower().strip()
                if key not in seen_values:
                    seen_values.add(key)
                    contacts.append(c)

        # 1. Check homepage
        response = await scraper.fetch(base_url)
        if response and response.status_code == 200:
            _add_unique(self._extract_contacts(response.text, "Website - Homepage", domain))
            _add_unique(self._extract_schema_contacts(response.text, "Website - Structured Data (Schema.org)"))

        # 2. Check contact/about pages
        for path in CONTACT_PAGE_PATHS:
            url = f"{base_url}{path}"
            response = await scraper.fetch(url)
            if response and response.status_code == 200:
                page_label = f"Website - {path.strip('/').replace('-', ' ').title()} Page"
                _add_unique(self._extract_contacts(response.text, page_label, domain))
                if contacts:
                    break

        # 3. Try social media profiles for contact info
        if response and response.status_code == 200:
            social_contacts = await self._extract_social_contacts(response.text, domain)
            _add_unique(social_contacts)

        return {"contacts": contacts[:20]}

    def _extract_contacts(self, html: str, source_label: str, domain: str) -> list[dict]:
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
                        "value": email.lower(),
                        "source": f"{source_label} (mailto link)",
                        "page_url": "",
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
                    "source": f"{source_label} (page text)",
                    "page_url": "",
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
                        "source": f"{source_label} (tel link)",
                        "page_url": "",
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
                    "source": f"{source_label} (page text)",
                    "page_url": "",
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

    def _extract_schema_contacts(self, html: str, source_label: str) -> list[dict]:
        """Extract contact info from JSON-LD structured data."""
        contacts = []
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
                        # Extract email from Organization/LocalBusiness
                        email = item.get("email")
                        if email and re.match(EMAIL_REGEX, email):
                            contacts.append({
                                "type": "email", "value": email.lower(),
                                "source": source_label, "page_url": "", "confidence": 0.95,
                            })
                        # Extract phone
                        phone = item.get("telephone")
                        if phone and len(re.sub(r"[^\d+]", "", phone)) >= 7:
                            contacts.append({
                                "type": "phone", "value": phone,
                                "source": source_label, "page_url": "", "confidence": 0.95,
                            })
                        # Check contactPoint
                        cp = item.get("contactPoint")
                        if isinstance(cp, dict):
                            cp = [cp]
                        if isinstance(cp, list):
                            for point in cp:
                                cp_phone = point.get("telephone")
                                cp_email = point.get("email")
                                if cp_phone and len(re.sub(r"[^\d+]", "", cp_phone)) >= 7:
                                    contacts.append({
                                        "type": "phone", "value": cp_phone,
                                        "source": source_label, "page_url": "", "confidence": 0.95,
                                    })
                                if cp_email and re.match(EMAIL_REGEX, cp_email):
                                    contacts.append({
                                        "type": "email", "value": cp_email.lower(),
                                        "source": source_label, "page_url": "", "confidence": 0.95,
                                    })
                except (json.JSONDecodeError, AttributeError):
                    pass
        except Exception:
            pass
        return contacts

    async def _extract_social_contacts(self, html: str, domain: str) -> list[dict]:
        """Try to extract contact info from linked social media profiles."""
        contacts = []
        soup = BeautifulSoup(html, "lxml")

        # Find Facebook URL and try to get email/phone from the about page
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "facebook.com/" in href and "/sharer" not in href and "/dialog/" not in href:
                try:
                    fb_about = href.rstrip("/") + "/about"
                    response = await scraper.fetch(fb_about)
                    if response and response.status_code == 200:
                        fb_text = response.text
                        emails = re.findall(EMAIL_REGEX, fb_text)
                        for email in emails:
                            if self._is_valid_email(email, domain):
                                contacts.append({
                                    "type": "email", "value": email.lower(),
                                    "source": "Social Media - Facebook",
                                    "page_url": fb_about, "confidence": 0.85,
                                })
                        phones_us = re.findall(PHONE_REGEX_US, fb_text)
                        phones_intl = re.findall(PHONE_REGEX_INTL, fb_text)
                        for phone in set(phones_us + phones_intl):
                            cleaned = re.sub(r"[^\d+]", "", phone)
                            if len(cleaned) >= 7:
                                contacts.append({
                                    "type": "phone", "value": phone.strip(),
                                    "source": "Social Media - Facebook",
                                    "page_url": fb_about, "confidence": 0.8,
                                })
                except Exception:
                    pass
                break  # Only try first Facebook link

        return contacts

    def _is_valid_email(self, email: str, domain: str) -> bool:
        email = email.lower().strip()
        if not re.match(EMAIL_REGEX, email):
            return False
        for blacklist_pattern in EMAIL_BLACKLIST_PATTERNS:
            if re.match(blacklist_pattern, email, re.IGNORECASE):
                return False
        return True
