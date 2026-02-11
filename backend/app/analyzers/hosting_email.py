from app.analyzers.base import BaseAnalyzer
from app.services.dns_service import dns_service
from app.services.scraper import scraper
from app.utils.patterns import (
    EMAIL_PROVIDER_PATTERNS,
    HOSTING_CNAME_PATTERNS,
    HOSTING_HEADER_PATTERNS,
    HOSTING_IP_PREFIXES,
    HOSTING_NS_PATTERNS,
)
from app.utils.url_helpers import get_base_url


class HostingEmailAnalyzer(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        records = await dns_service.get_all_records(domain)

        # Determine hosting provider
        hosting_provider = None
        cdn_provider = None
        ip_address = None

        # Check A records / IP ranges
        a_records = records.get("a_records", [])
        if a_records:
            ip_address = a_records[0]
            hosting_provider = self._match_ip(ip_address)

        # Check NS records
        ns_records = records.get("ns_records", [])
        if not hosting_provider:
            hosting_provider = self._match_ns(ns_records)

        # Check CNAME records
        cname_records = records.get("cname_records", [])
        cname_host = self._match_cname(cname_records)
        if cname_host:
            if not hosting_provider:
                hosting_provider = cname_host

        # Check HTTP headers for CDN / hosting hints
        base_url = get_base_url(domain)
        response = await scraper.fetch(base_url)
        if response:
            header_host, header_cdn = self._check_headers(dict(response.headers))
            if header_cdn:
                cdn_provider = header_cdn
            if not hosting_provider and header_host:
                hosting_provider = header_host

        # Determine email provider from MX records
        mx_records = records.get("mx_records", [])
        email_provider = self._match_email_provider(mx_records)

        # Try WHOIS for registrar info
        registrar = None
        registration_date = None
        try:
            import whois
            w = await self._whois_lookup(domain)
            if w:
                registrar = w.get("registrar")
                reg_date = w.get("creation_date")
                if isinstance(reg_date, list):
                    reg_date = reg_date[0]
                registration_date = str(reg_date) if reg_date else None
        except Exception:
            pass

        return {
            "hosting_provider": hosting_provider,
            "ip_address": ip_address,
            "nameservers": ns_records,
            "cdn_provider": cdn_provider,
            "email_provider": email_provider,
            "mx_records": mx_records,
            "registrar": registrar,
            "registration_date": registration_date,
        }

    def _match_ip(self, ip: str) -> str | None:
        for provider, prefixes in HOSTING_IP_PREFIXES.items():
            for prefix in prefixes:
                if ip.startswith(prefix):
                    return provider
        return None

    def _match_ns(self, ns_records: list[str]) -> str | None:
        for provider, patterns in HOSTING_NS_PATTERNS.items():
            for ns in ns_records:
                ns_lower = ns.lower()
                for pattern in patterns:
                    if pattern in ns_lower:
                        return provider
        return None

    def _match_cname(self, cname_records: list[str]) -> str | None:
        for provider, patterns in HOSTING_CNAME_PATTERNS.items():
            for cname in cname_records:
                cname_lower = cname.lower()
                for pattern in patterns:
                    if pattern in cname_lower:
                        return provider
        return None

    def _check_headers(self, headers: dict) -> tuple[str | None, str | None]:
        hosting = None
        cdn = None
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}

        for provider, header_names in HOSTING_HEADER_PATTERNS.items():
            for header_name in header_names:
                header_name_lower = header_name.lower()
                # Check both as header key and header value
                if header_name_lower in headers_lower:
                    if provider in ("cloudflare", "fastly", "akamai"):
                        cdn = provider
                    else:
                        hosting = provider
                    break
                for k, v in headers_lower.items():
                    if header_name_lower in k or header_name_lower in v:
                        if provider in ("cloudflare", "fastly", "akamai"):
                            cdn = provider
                        else:
                            hosting = provider
                        break

        return hosting, cdn

    def _match_email_provider(self, mx_records: list[str]) -> str | None:
        for mx in mx_records:
            mx_lower = mx.lower()
            for provider, patterns in EMAIL_PROVIDER_PATTERNS.items():
                for pattern in patterns:
                    if pattern in mx_lower:
                        return provider
        return None

    async def _whois_lookup(self, domain: str) -> dict | None:
        import asyncio
        try:
            import whois
            result = await asyncio.to_thread(whois.whois, domain)
            return {
                "registrar": result.registrar,
                "creation_date": result.creation_date,
            }
        except Exception:
            return None
