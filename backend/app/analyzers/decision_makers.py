import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from app.analyzers.base import BaseAnalyzer
from app.services.scraper import scraper
from app.utils.patterns import (
    DECISION_MAKER_TITLES,
    EMAIL_PATTERN_TEMPLATES,
    TEAM_PAGE_PATHS,
)
from app.utils.url_helpers import get_base_url


class DecisionMakerAnalyzer(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        people = []

        # Try to find team/about pages
        for path in TEAM_PAGE_PATHS:
            url = f"{base_url}{path}"
            response = await scraper.fetch(url)
            if response and response.status_code == 200:
                found = self._extract_people(response.text, url, domain)
                people.extend(found)
                if people:
                    break

        # Also check homepage for structured data
        response = await scraper.fetch(base_url)
        if response and response.status_code == 200:
            schema_people = self._extract_schema_people(response.text, domain)
            # Merge, avoiding duplicates
            existing_names = {p["name"].lower() for p in people if p["name"]}
            for sp in schema_people:
                if sp["name"] and sp["name"].lower() not in existing_names:
                    people.append(sp)

        # Deduplicate and limit
        seen = set()
        unique_people = []
        for person in people:
            key = (person.get("name", "").lower(), person.get("title", "").lower())
            if key not in seen and person.get("name"):
                seen.add(key)
                unique_people.append(person)

        return {"decision_makers": unique_people[:10]}

    def _extract_people(self, html: str, page_url: str, domain: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        people = []

        # Strategy 1: Look for structured team member blocks
        team_selectors = [
            {"class_": re.compile(r"team|staff|leadership|member|people|bio", re.I)},
        ]

        for selector in team_selectors:
            blocks = soup.find_all(["div", "section", "article", "li"], **selector)
            for block in blocks:
                person = self._parse_person_block(block, domain)
                if person:
                    person["source"] = "website_team_page"
                    people.append(person)

        # Strategy 2: Look for heading + paragraph pairs
        if not people:
            for heading in soup.find_all(["h2", "h3", "h4"]):
                text = heading.get_text(strip=True)
                next_elem = heading.find_next_sibling(["p", "span", "div"])
                if next_elem:
                    title_text = next_elem.get_text(strip=True)
                    if self._is_likely_name(text) and self._contains_title(title_text):
                        person = self._build_person(text, title_text, domain)
                        person["source"] = "website_about_page"
                        people.append(person)

        return people

    def _parse_person_block(self, block, domain: str) -> dict | None:
        headings = block.find_all(["h2", "h3", "h4", "h5", "strong"])
        paragraphs = block.find_all(["p", "span"])

        name = None
        title = None

        for h in headings:
            text = h.get_text(strip=True)
            if self._is_likely_name(text):
                name = text
                break

        for p in paragraphs:
            text = p.get_text(strip=True)
            if self._contains_title(text):
                title = text
                break

        if name:
            return self._build_person(name, title, domain)
        return None

    def _build_person(self, name: str, title: str | None, domain: str) -> dict:
        # Generate LinkedIn search URL
        linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={quote(name)}"

        # Generate email guesses
        email = self._guess_email(name, domain)

        confidence = 0.7
        if title and self._is_high_value_title(title):
            confidence = 0.9

        return {
            "name": name,
            "title": title,
            "linkedin_url": linkedin_url,
            "email": email,
            "source": "website",
            "confidence": confidence,
        }

    def _guess_email(self, name: str, domain: str) -> str | None:
        parts = name.lower().strip().split()
        if len(parts) < 2:
            return None
        first = re.sub(r"[^a-z]", "", parts[0])
        last = re.sub(r"[^a-z]", "", parts[-1])
        if first and last:
            return f"{first}.{last}@{domain}"
        return None

    def _is_likely_name(self, text: str) -> bool:
        text = text.strip()
        if not text or len(text) > 60 or len(text) < 3:
            return False
        words = text.split()
        if len(words) < 2 or len(words) > 5:
            return False
        # Most name words should start with uppercase
        capitalized = sum(1 for w in words if w[0].isupper())
        return capitalized >= len(words) * 0.5

    def _contains_title(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        return any(title in text_lower for title in DECISION_MAKER_TITLES)

    def _is_high_value_title(self, title: str) -> bool:
        high_value = ["ceo", "founder", "co-founder", "cmo", "marketing director",
                      "head of marketing", "head of e-commerce", "head of ecommerce"]
        title_lower = title.lower()
        return any(t in title_lower for t in high_value)

    def _extract_schema_people(self, html: str, domain: str) -> list[dict]:
        import json
        people = []
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
                        if item.get("@type") == "Person":
                            name = item.get("name", "")
                            title = item.get("jobTitle", "")
                            if name:
                                person = self._build_person(name, title, domain)
                                person["source"] = "schema_org"
                                people.append(person)
                except (json.JSONDecodeError, AttributeError):
                    pass
        except Exception:
            pass
        return people
