from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# --- Lead ---

class LeadCreate(BaseModel):
    domain: str
    url: Optional[str] = None
    company_name: Optional[str] = None
    source: str = "manual"

    @field_validator("domain")
    @classmethod
    def clean_domain(cls, v: str) -> str:
        v = v.strip().lower()
        for prefix in ("https://", "http://", "www."):
            if v.startswith(prefix):
                v = v[len(prefix):]
        return v.rstrip("/")


class LeadBulkCreate(BaseModel):
    domains: list[str]
    source: str = "csv_upload"


class LeadResponse(BaseModel):
    id: int
    domain: str
    url: Optional[str] = None
    company_name: Optional[str] = None
    status: str
    source: str
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EcommerceResponse(BaseModel):
    is_ecommerce: bool
    platform: Optional[str] = None
    confidence_score: float
    evidence: list = []
    has_cart: bool = False
    has_product_pages: bool = False
    has_checkout: bool = False

    model_config = {"from_attributes": True}


class MarketingToolsResponse(BaseModel):
    has_google_analytics: bool = False
    ga_version: Optional[str] = None
    ga_id: Optional[str] = None
    has_gtm: bool = False
    gtm_id: Optional[str] = None
    has_gsc: bool = False
    has_facebook_pixel: bool = False
    fb_pixel_id: Optional[str] = None
    has_tiktok_pixel: bool = False
    tiktok_pixel_id: Optional[str] = None
    has_hotjar: bool = False
    has_clarity: bool = False
    has_mixpanel: bool = False
    has_segment: bool = False
    has_heap: bool = False
    has_amplitude: bool = False
    all_detected_tools: list = []

    model_config = {"from_attributes": True}


class HostingEmailResponse(BaseModel):
    hosting_provider: Optional[str] = None
    ip_address: Optional[str] = None
    nameservers: list = []
    cdn_provider: Optional[str] = None
    email_provider: Optional[str] = None
    mx_records: list = []
    registrar: Optional[str] = None
    registration_date: Optional[str] = None

    model_config = {"from_attributes": True}


class AdActivityResponse(BaseModel):
    is_running_google_ads: bool = False
    google_ads_count: int = 0
    google_advertiser_id: Optional[str] = None
    is_running_meta_ads: bool = False
    meta_ads_count: int = 0
    meta_page_id: Optional[str] = None
    is_running_tiktok_ads: bool = False
    tiktok_ads_count: int = 0
    ad_details: dict = {}

    model_config = {"from_attributes": True}


class SocialMediaResponse(BaseModel):
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    youtube_url: Optional[str] = None
    instagram_active: Optional[bool] = None
    facebook_active: Optional[bool] = None
    tiktok_active: Optional[bool] = None
    twitter_active: Optional[bool] = None
    linkedin_active: Optional[bool] = None
    activity_details: dict = {}

    model_config = {"from_attributes": True}


class DecisionMakerResponse(BaseModel):
    id: int
    name: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    confidence: float = 0.0

    model_config = {"from_attributes": True}


class ContactInfoResponse(BaseModel):
    id: int
    type: str
    value: str
    source: Optional[str] = None
    page_url: Optional[str] = None
    confidence: float = 0.0

    model_config = {"from_attributes": True}


class PitchResponse(BaseModel):
    gaps_identified: list = []
    recommendations: list = []
    pitch_text: Optional[str] = None
    pitch_subject_line: Optional[str] = None
    generated_at: Optional[datetime] = None
    edited: bool = False

    model_config = {"from_attributes": True}


class PitchUpdate(BaseModel):
    pitch_text: Optional[str] = None
    pitch_subject_line: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    lead_id: int
    overall_status: str
    modules: dict[str, str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LeadDetailResponse(LeadResponse):
    ecommerce: Optional[EcommerceResponse] = None
    marketing_tools: Optional[MarketingToolsResponse] = None
    hosting_email: Optional[HostingEmailResponse] = None
    ad_activity: Optional[AdActivityResponse] = None
    social_media: Optional[SocialMediaResponse] = None
    decision_makers: list[DecisionMakerResponse] = []
    contacts: list[ContactInfoResponse] = []
    pitch: Optional[PitchResponse] = None


class DiscoverySearchRequest(BaseModel):
    query: str
    max_results: int = 20


class DiscoveryResult(BaseModel):
    domain: str
    url: str
    title: str
    snippet: str


class DiscoveryImportRequest(BaseModel):
    domains: list[str]


class BulkAnalysisRequest(BaseModel):
    lead_ids: list[int]


class StatsResponse(BaseModel):
    total_leads: int = 0
    analyzed: int = 0
    pending: int = 0
    analyzing: int = 0
    failed: int = 0
    ecommerce_confirmed: int = 0
    with_gaps: int = 0
