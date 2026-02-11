import re
from urllib.parse import urlparse

import tldextract


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


def extract_domain(url: str) -> str:
    ext = tldextract.extract(url)
    if ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    return ext.domain


def ensure_scheme(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url


def is_valid_domain(domain: str) -> bool:
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))


def get_base_url(domain: str) -> str:
    return f"https://{domain}"


def resolve_relative_url(base_url: str, path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"
