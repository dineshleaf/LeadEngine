from app.analyzers.base import BaseAnalyzer


# Gap rules: each rule checks analysis data and identifies a gap
GAP_RULES = [
    {
        "key": "no_google_analytics",
        "check": lambda mt, **_: mt and not mt.get("has_google_analytics"),
        "gap": "No Google Analytics detected",
        "category": "analytics",
        "severity": "high",
        "recommendation": "Implement GA4 to track website traffic, user behavior, and conversion funnels. This is essential for data-driven marketing decisions.",
    },
    {
        "key": "no_gtm",
        "check": lambda mt, **_: mt and not mt.get("has_gtm"),
        "gap": "No Google Tag Manager",
        "category": "analytics",
        "severity": "medium",
        "recommendation": "Implement GTM to centrally manage all tracking pixels and marketing tags without requiring code changes for each update.",
    },
    {
        "key": "no_gsc",
        "check": lambda mt, **_: mt and not mt.get("has_gsc"),
        "gap": "No Google Search Console verification",
        "category": "seo",
        "severity": "medium",
        "recommendation": "Set up Google Search Console to monitor search performance, index coverage, and identify SEO opportunities.",
    },
    {
        "key": "no_facebook_pixel",
        "check": lambda mt, **_: mt and not mt.get("has_facebook_pixel"),
        "gap": "No Facebook/Meta Pixel installed",
        "category": "advertising",
        "severity": "high",
        "recommendation": "Install Meta Pixel to track conversions, build retargeting audiences, and optimize ad delivery for better ROAS.",
    },
    {
        "key": "no_tiktok_pixel",
        "check": lambda mt, **_: mt and not mt.get("has_tiktok_pixel"),
        "gap": "No TikTok Pixel installed",
        "category": "advertising",
        "severity": "medium",
        "recommendation": "Install TikTok Pixel to measure ad performance, optimize campaigns, and reach younger demographics effectively.",
    },
    {
        "key": "no_heatmaps",
        "check": lambda mt, **_: mt and not mt.get("has_clarity") and not mt.get("has_hotjar"),
        "gap": "No heatmap/session recording tool (Clarity or Hotjar)",
        "category": "analytics",
        "severity": "medium",
        "recommendation": "Implement Microsoft Clarity (free) or Hotjar to visualize user behavior through heatmaps and session recordings, identifying UX issues that hurt conversions.",
    },
    {
        "key": "no_google_ads",
        "check": lambda ad, **_: ad and not ad.get("is_running_google_ads"),
        "gap": "Not running Google Ads",
        "category": "advertising",
        "severity": "high",
        "recommendation": "Launch Google Shopping and Search campaigns to capture high-intent purchase traffic and drive immediate revenue.",
    },
    {
        "key": "no_meta_ads",
        "check": lambda ad, **_: ad and not ad.get("is_running_meta_ads"),
        "gap": "Not running Meta/Facebook Ads",
        "category": "advertising",
        "severity": "medium",
        "recommendation": "Start Meta advertising to build brand awareness, reach new audiences, and retarget website visitors.",
    },
    {
        "key": "no_tiktok_ads",
        "check": lambda ad, **_: ad and not ad.get("is_running_tiktok_ads"),
        "gap": "Not running TikTok Ads",
        "category": "advertising",
        "severity": "low",
        "recommendation": "Consider TikTok advertising to engage younger demographics with creative video content and drive social commerce.",
    },
    {
        "key": "no_instagram",
        "check": lambda sm, **_: sm and not sm.get("instagram_url"),
        "gap": "No Instagram presence found",
        "category": "social",
        "severity": "high",
        "recommendation": "Build an Instagram presence with product showcases, user-generated content, and Stories to drive brand awareness and engagement.",
    },
    {
        "key": "inactive_instagram",
        "check": lambda sm, **_: sm and sm.get("instagram_url") and sm.get("instagram_active") is False,
        "gap": "Instagram account exists but appears inactive",
        "category": "social",
        "severity": "medium",
        "recommendation": "Revitalize your Instagram with a consistent posting schedule, engaging Reels, and interactive Stories to rebuild audience engagement.",
    },
    {
        "key": "no_facebook",
        "check": lambda sm, **_: sm and not sm.get("facebook_url"),
        "gap": "No Facebook page found",
        "category": "social",
        "severity": "medium",
        "recommendation": "Create a Facebook Business page to leverage the platform's massive user base, run targeted ads, and provide social proof.",
    },
    {
        "key": "no_tiktok_social",
        "check": lambda sm, **_: sm and not sm.get("tiktok_url"),
        "gap": "No TikTok presence found",
        "category": "social",
        "severity": "low",
        "recommendation": "Consider creating a TikTok account to tap into organic viral potential and reach Gen Z and Millennial shoppers.",
    },
    {
        "key": "no_linkedin",
        "check": lambda sm, **_: sm and not sm.get("linkedin_url"),
        "gap": "No LinkedIn company page found",
        "category": "social",
        "severity": "low",
        "recommendation": "Create a LinkedIn company page to build B2B credibility, attract talent, and engage with business partners.",
    },
]


class PitchGenerator(BaseAnalyzer):
    async def analyze(self, domain: str, **analysis_data) -> dict:
        # This analyzer is special - it takes pre-computed analysis data
        mt = analysis_data.get("marketing_tools", {})
        ad = analysis_data.get("ad_activity", {})
        sm = analysis_data.get("social_media", {})
        ec = analysis_data.get("ecommerce", {})
        he = analysis_data.get("hosting_email", {})

        # Identify gaps
        gaps = []
        recommendations = []

        for rule in GAP_RULES:
            try:
                if rule["check"](mt=mt, ad=ad, sm=sm, ec=ec, he=he):
                    gaps.append(rule["gap"])
                    recommendations.append({
                        "gap": rule["gap"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "recommendation": rule["recommendation"],
                    })
            except Exception:
                continue

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: severity_order.get(r["severity"], 3))

        # Generate positive observations
        positives = self._find_positives(ec, mt, ad, sm)

        # Generate pitch text
        pitch_text = self._generate_pitch(
            domain=domain,
            company_name=analysis_data.get("company_name", domain),
            gaps=gaps,
            recommendations=recommendations,
            positives=positives,
        )

        # Generate subject line
        primary_category = recommendations[0]["category"] if recommendations else "growth"
        subject_line = self._generate_subject(
            analysis_data.get("company_name", domain), primary_category
        )

        return {
            "gaps_identified": gaps,
            "recommendations": [r["recommendation"] for r in recommendations],
            "pitch_text": pitch_text,
            "pitch_subject_line": subject_line,
        }

    def _find_positives(self, ec: dict, mt: dict, ad: dict, sm: dict) -> list[str]:
        positives = []
        if ec and ec.get("is_ecommerce"):
            platform = ec.get("platform", "")
            if platform and platform != "unknown":
                positives.append(f"your well-built {platform.title()} store")
            else:
                positives.append("your e-commerce store")
        if mt:
            if mt.get("has_google_analytics"):
                positives.append("your use of Google Analytics for data tracking")
            if mt.get("has_gtm"):
                positives.append("your Google Tag Manager setup")
        if ad:
            if ad.get("is_running_google_ads"):
                positives.append("your active Google Ads campaigns")
            if ad.get("is_running_meta_ads"):
                positives.append("your Meta advertising presence")
        if sm:
            active_platforms = []
            if sm.get("instagram_active"):
                active_platforms.append("Instagram")
            if sm.get("facebook_active"):
                active_platforms.append("Facebook")
            if sm.get("tiktok_active"):
                active_platforms.append("TikTok")
            if active_platforms:
                positives.append(f"your active presence on {', '.join(active_platforms)}")
        return positives

    def _generate_pitch(
        self,
        domain: str,
        company_name: str,
        gaps: list[str],
        recommendations: list[dict],
        positives: list[str],
    ) -> str:
        positive_text = positives[0] if positives else "your online store"

        # Gap summary (top 3)
        top_gaps = gaps[:3]
        gap_bullets = "\n".join(f"  - {g}" for g in top_gaps)

        # Top recommendations (top 3)
        top_recs = recommendations[:3]
        rec_bullets = "\n".join(
            f"  {i+1}. {r['recommendation']}" for i, r in enumerate(top_recs)
        )

        pitch = f"""Hi,

I came across {company_name} and was impressed by {positive_text}.

After reviewing your online presence, I noticed a few opportunities that could significantly boost your e-commerce performance:

{gap_bullets}

Here are my top {len(top_recs)} recommendations:

{rec_bullets}

I've helped similar e-commerce brands improve their {recommendations[0]['category'] if recommendations else 'digital marketing'} strategy and drive measurable growth. Would you be open to a quick 15-minute call this week to discuss how we can help {company_name} achieve similar results?

Looking forward to hearing from you.

Best regards"""

        return pitch

    def _generate_subject(self, company_name: str, primary_category: str) -> str:
        category_labels = {
            "analytics": "data-driven growth",
            "advertising": "advertising performance",
            "social": "social media presence",
            "seo": "search visibility",
        }
        label = category_labels.get(primary_category, "digital growth")
        return f"Quick thought on {company_name}'s {label}"
