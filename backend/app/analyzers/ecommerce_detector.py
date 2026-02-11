import json
import re

from bs4 import BeautifulSoup

from app.analyzers.base import BaseAnalyzer
from app.services.scraper import scraper
from app.utils.patterns import (
    ECOMMERCE_PROBE_PATHS,
    ECOMMERCE_SCHEMA_TYPES,
    ECOMMERCE_SIGNATURES,
    GENERIC_ECOMMERCE_SIGNALS,
)
from app.utils.url_helpers import get_base_url


class EcommerceDetector(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        evidence = []
        platform = None
        confidence = 0.0

        # Fetch homepage
        response = await scraper.fetch(base_url)
        if not response or response.status_code >= 400:
            return self._empty_result()

        html = response.text
        headers = dict(response.headers)

        # Check HTTP headers for platform hints
        platform, header_evidence = self._check_headers(headers)
        evidence.extend(header_evidence)

        # Parse HTML
        soup = BeautifulSoup(html, "lxml")

        # Check for platform signatures in HTML
        if not platform:
            platform, html_evidence = self._check_html_signatures(html, soup)
            evidence.extend(html_evidence)

        # Check meta generator tag
        if not platform:
            gen_platform, gen_evidence = self._check_meta_generator(soup)
            if gen_platform:
                platform = gen_platform
                evidence.extend(gen_evidence)

        # Check for generic e-commerce signals
        generic_evidence = self._check_generic_signals(html, soup)
        evidence.extend(generic_evidence)

        # Check for Schema.org Product markup
        schema_evidence = self._check_schema_markup(html)
        evidence.extend(schema_evidence)

        # Probe e-commerce paths
        path_results = await self._probe_paths(base_url)
        evidence.extend(path_results["evidence"])

        # Calculate confidence
        is_ecommerce = False
        if platform:
            confidence = 0.9
            is_ecommerce = True
        elif len(evidence) >= 3:
            confidence = 0.7
            is_ecommerce = True
            platform = "custom"
        elif len(evidence) >= 1:
            confidence = 0.4
            is_ecommerce = True
            platform = "unknown"
        else:
            confidence = 0.0

        return {
            "is_ecommerce": is_ecommerce,
            "platform": platform,
            "confidence_score": round(confidence, 2),
            "evidence": evidence,
            "has_cart": path_results.get("has_cart", False),
            "has_product_pages": path_results.get("has_product_pages", False),
            "has_checkout": path_results.get("has_checkout", False),
        }

    def _check_headers(self, headers: dict) -> tuple[str | None, list[str]]:
        evidence = []
        headers_lower = {k.lower(): v for k, v in headers.items()}

        for platform, sigs in ECOMMERCE_SIGNATURES.items():
            for header_pattern in sigs.get("headers", []):
                for header_key in headers_lower:
                    if header_pattern.lower() in header_key:
                        evidence.append(f"HTTP header '{header_key}' indicates {platform}")
                        return platform, evidence
        return None, evidence

    def _check_html_signatures(self, html: str, soup: BeautifulSoup) -> tuple[str | None, list[str]]:
        evidence = []
        html_lower = html.lower()

        for platform, sigs in ECOMMERCE_SIGNATURES.items():
            matches = 0
            for pattern in sigs.get("html_patterns", []):
                if pattern.lower() in html_lower:
                    matches += 1
                    evidence.append(f"HTML pattern '{pattern}' found ({platform})")

            if matches >= 2:
                return platform, evidence

        return None, evidence

    def _check_meta_generator(self, soup: BeautifulSoup) -> tuple[str | None, list[str]]:
        meta_gen = soup.find("meta", attrs={"name": "generator"})
        if meta_gen:
            content = (meta_gen.get("content", "") or "").lower()
            for platform, sigs in ECOMMERCE_SIGNATURES.items():
                gen = sigs.get("meta_generator", "")
                if gen and gen.lower() in content:
                    return platform, [f"Meta generator: {content}"]
        return None, []

    def _check_generic_signals(self, html: str, soup: BeautifulSoup) -> list[str]:
        evidence = []
        html_lower = html.lower()

        for signal in GENERIC_ECOMMERCE_SIGNALS:
            if signal in html_lower:
                evidence.append(f"Generic e-commerce signal: '{signal}'")

        # Check og:type
        og_type = soup.find("meta", property="og:type")
        if og_type and "product" in (og_type.get("content", "") or "").lower():
            evidence.append("Open Graph type: product")

        return evidence

    def _check_schema_markup(self, html: str) -> list[str]:
        evidence = []
        try:
            ld_json_pattern = re.findall(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html, re.DOTALL | re.IGNORECASE,
            )
            for block in ld_json_pattern:
                try:
                    data = json.loads(block)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        schema_type = item.get("@type", "")
                        if isinstance(schema_type, list):
                            types = schema_type
                        else:
                            types = [schema_type]
                        for t in types:
                            if t in ECOMMERCE_SCHEMA_TYPES:
                                evidence.append(f"Schema.org @type: {t}")
                except (json.JSONDecodeError, AttributeError):
                    pass
        except Exception:
            pass
        return evidence

    async def _probe_paths(self, base_url: str) -> dict:
        result = {"evidence": [], "has_cart": False, "has_product_pages": False, "has_checkout": False}

        for path in ECOMMERCE_PROBE_PATHS:
            url = f"{base_url}{path}"
            response = await scraper.fetch(url)
            if response and response.status_code == 200:
                result["evidence"].append(f"Path {path} returned 200 OK")
                if "cart" in path:
                    result["has_cart"] = True
                elif "product" in path or "collection" in path or "shop" in path:
                    result["has_product_pages"] = True
                elif "checkout" in path:
                    result["has_checkout"] = True

        return result

    def _empty_result(self) -> dict:
        return {
            "is_ecommerce": False,
            "platform": None,
            "confidence_score": 0.0,
            "evidence": ["Could not fetch website"],
            "has_cart": False,
            "has_product_pages": False,
            "has_checkout": False,
        }
