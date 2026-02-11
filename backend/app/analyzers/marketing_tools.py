import re

from bs4 import BeautifulSoup

from app.analyzers.base import BaseAnalyzer
from app.services.scraper import scraper
from app.utils.patterns import MARKETING_TOOL_PATTERNS
from app.utils.url_helpers import get_base_url


class MarketingToolsAnalyzer(BaseAnalyzer):
    async def analyze(self, domain: str) -> dict:
        base_url = get_base_url(domain)
        response = await scraper.fetch(base_url)

        if not response or response.status_code >= 400:
            return self._empty_result()

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # Collect all script sources and inline scripts
        script_srcs = []
        inline_scripts = []
        for script_tag in soup.find_all("script"):
            src = script_tag.get("src", "")
            if src:
                script_srcs.append(src)
            text = script_tag.string or ""
            if text.strip():
                inline_scripts.append(text)

        # Collect noscript content
        noscript_content = " ".join(
            tag.decode_contents() for tag in soup.find_all("noscript")
        )

        # Collect meta tags
        meta_tags = " ".join(str(tag) for tag in soup.find_all("meta"))

        # Detect each tool
        detected_tools = []
        result = {}

        for tool_name, patterns in MARKETING_TOOL_PATTERNS.items():
            found = False
            tool_id = None

            # Check script src patterns
            for src_pattern in patterns.get("script_src", []):
                for src in script_srcs:
                    if re.search(src_pattern, src, re.IGNORECASE):
                        found = True
                        break
                if found:
                    break

            # Check inline script patterns
            if not found:
                for inline_pattern in patterns.get("inline", []):
                    for script_text in inline_scripts:
                        if re.search(inline_pattern, script_text, re.IGNORECASE):
                            found = True
                            break
                    if found:
                        break

            # Check noscript patterns
            if not found:
                for ns_pattern in patterns.get("noscript", []):
                    if re.search(ns_pattern, noscript_content, re.IGNORECASE):
                        found = True
                        break

            # Check meta tag patterns
            if not found:
                for meta_pattern in patterns.get("meta", []):
                    if re.search(meta_pattern, meta_tags, re.IGNORECASE):
                        found = True
                        break

            # Extract ID if found
            if found and "id_pattern" in patterns:
                full_text = " ".join(inline_scripts) + " " + " ".join(script_srcs) + " " + noscript_content
                match = re.search(patterns["id_pattern"], full_text, re.IGNORECASE)
                if match:
                    tool_id = match.group(1) if match.lastindex else match.group(0)

            if found:
                detected_tools.append(tool_name)

            result[tool_name] = {"found": found, "id": tool_id}

        # Map to response fields
        ga4 = result.get("google_analytics_ga4", {})
        ua = result.get("google_analytics_ua", {})
        has_ga = ga4.get("found", False) or ua.get("found", False)
        ga_version = None
        ga_id = None
        if ga4.get("found") and ua.get("found"):
            ga_version = "both"
            ga_id = ga4.get("id") or ua.get("id")
        elif ga4.get("found"):
            ga_version = "GA4"
            ga_id = ga4.get("id")
        elif ua.get("found"):
            ga_version = "UA"
            ga_id = ua.get("id")

        gtm = result.get("google_tag_manager", {})
        fb = result.get("facebook_pixel", {})
        tt = result.get("tiktok_pixel", {})

        return {
            "has_google_analytics": has_ga,
            "ga_version": ga_version,
            "ga_id": ga_id,
            "has_gtm": gtm.get("found", False),
            "gtm_id": gtm.get("id"),
            "has_gsc": result.get("google_search_console", {}).get("found", False),
            "has_facebook_pixel": fb.get("found", False),
            "fb_pixel_id": fb.get("id"),
            "has_tiktok_pixel": tt.get("found", False),
            "tiktok_pixel_id": tt.get("id"),
            "has_hotjar": result.get("hotjar", {}).get("found", False),
            "has_clarity": result.get("microsoft_clarity", {}).get("found", False),
            "has_mixpanel": result.get("mixpanel", {}).get("found", False),
            "has_segment": result.get("segment", {}).get("found", False),
            "has_heap": result.get("heap", {}).get("found", False),
            "has_amplitude": result.get("amplitude", {}).get("found", False),
            "all_detected_tools": detected_tools,
        }

    def _empty_result(self) -> dict:
        return {
            "has_google_analytics": False,
            "ga_version": None,
            "ga_id": None,
            "has_gtm": False,
            "gtm_id": None,
            "has_gsc": False,
            "has_facebook_pixel": False,
            "fb_pixel_id": None,
            "has_tiktok_pixel": False,
            "tiktok_pixel_id": None,
            "has_hotjar": False,
            "has_clarity": False,
            "has_mixpanel": False,
            "has_segment": False,
            "has_heap": False,
            "has_amplitude": False,
            "all_detected_tools": [],
        }
