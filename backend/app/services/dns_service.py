import asyncio
import logging
from typing import Optional

import dns.resolver

logger = logging.getLogger(__name__)


def _resolve_sync(domain: str, rdtype: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(domain, rdtype)
        return [str(rdata) for rdata in answers]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers,
            dns.resolver.Timeout, dns.exception.DNSException):
        return []


class DNSService:
    async def lookup_a(self, domain: str) -> list[str]:
        return await asyncio.to_thread(_resolve_sync, domain, "A")

    async def lookup_aaaa(self, domain: str) -> list[str]:
        return await asyncio.to_thread(_resolve_sync, domain, "AAAA")

    async def lookup_mx(self, domain: str) -> list[str]:
        return await asyncio.to_thread(_resolve_sync, domain, "MX")

    async def lookup_ns(self, domain: str) -> list[str]:
        return await asyncio.to_thread(_resolve_sync, domain, "NS")

    async def lookup_cname(self, domain: str) -> list[str]:
        return await asyncio.to_thread(_resolve_sync, domain, "CNAME")

    async def lookup_txt(self, domain: str) -> list[str]:
        return await asyncio.to_thread(_resolve_sync, domain, "TXT")

    async def get_all_records(self, domain: str) -> dict:
        results = await asyncio.gather(
            self.lookup_a(domain),
            self.lookup_mx(domain),
            self.lookup_ns(domain),
            self.lookup_cname(domain),
            self.lookup_txt(domain),
            return_exceptions=True,
        )

        def safe_result(r):
            if isinstance(r, Exception):
                return []
            return r

        return {
            "a_records": safe_result(results[0]),
            "mx_records": safe_result(results[1]),
            "ns_records": safe_result(results[2]),
            "cname_records": safe_result(results[3]),
            "txt_records": safe_result(results[4]),
        }


dns_service = DNSService()
