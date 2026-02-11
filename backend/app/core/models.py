from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow():
    return datetime.utcnow()


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    url = Column(String(2048))
    company_name = Column(String(255))
    status = Column(String(50), default="pending")
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    ecommerce = relationship(
        "EcommerceData", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )
    marketing_tools = relationship(
        "MarketingToolsData", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )
    hosting_email = relationship(
        "HostingEmailData", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )
    ad_activity = relationship(
        "AdActivityData", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )
    social_media = relationship(
        "SocialMediaData", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )
    decision_makers = relationship(
        "DecisionMaker", back_populates="lead", cascade="all, delete-orphan"
    )
    contacts = relationship(
        "ContactInfo", back_populates="lead", cascade="all, delete-orphan"
    )
    pitch = relationship(
        "Pitch", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )
    analysis_progress = relationship(
        "AnalysisProgress", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )


class EcommerceData(Base):
    __tablename__ = "ecommerce_data"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)
    is_ecommerce = Column(Boolean, default=False)
    platform = Column(String(100))
    confidence_score = Column(Float, default=0.0)
    evidence = Column(JSON, default=list)
    has_cart = Column(Boolean, default=False)
    has_product_pages = Column(Boolean, default=False)
    has_checkout = Column(Boolean, default=False)
    detected_at = Column(DateTime, default=utcnow)

    lead = relationship("Lead", back_populates="ecommerce")


class MarketingToolsData(Base):
    __tablename__ = "marketing_tools_data"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)

    has_google_analytics = Column(Boolean, default=False)
    ga_version = Column(String(10))
    ga_id = Column(String(50))
    has_gtm = Column(Boolean, default=False)
    gtm_id = Column(String(50))
    has_gsc = Column(Boolean, default=False)

    has_facebook_pixel = Column(Boolean, default=False)
    fb_pixel_id = Column(String(50))
    has_tiktok_pixel = Column(Boolean, default=False)
    tiktok_pixel_id = Column(String(50))

    has_hotjar = Column(Boolean, default=False)
    has_clarity = Column(Boolean, default=False)
    has_mixpanel = Column(Boolean, default=False)
    has_segment = Column(Boolean, default=False)
    has_heap = Column(Boolean, default=False)
    has_amplitude = Column(Boolean, default=False)

    all_detected_tools = Column(JSON, default=list)
    detected_at = Column(DateTime, default=utcnow)

    lead = relationship("Lead", back_populates="marketing_tools")


class HostingEmailData(Base):
    __tablename__ = "hosting_email_data"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)

    hosting_provider = Column(String(100))
    ip_address = Column(String(45))
    nameservers = Column(JSON, default=list)
    cdn_provider = Column(String(100))

    email_provider = Column(String(100))
    mx_records = Column(JSON, default=list)

    registrar = Column(String(200))
    registration_date = Column(String(50))

    detected_at = Column(DateTime, default=utcnow)

    lead = relationship("Lead", back_populates="hosting_email")


class AdActivityData(Base):
    __tablename__ = "ad_activity_data"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)

    is_running_google_ads = Column(Boolean, default=False)
    google_ads_count = Column(Integer, default=0)
    google_advertiser_id = Column(String(100))

    is_running_meta_ads = Column(Boolean, default=False)
    meta_ads_count = Column(Integer, default=0)
    meta_page_id = Column(String(100))

    is_running_tiktok_ads = Column(Boolean, default=False)
    tiktok_ads_count = Column(Integer, default=0)

    ad_details = Column(JSON, default=dict)
    detected_at = Column(DateTime, default=utcnow)

    lead = relationship("Lead", back_populates="ad_activity")


class SocialMediaData(Base):
    __tablename__ = "social_media_data"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)

    instagram_url = Column(String(500))
    facebook_url = Column(String(500))
    tiktok_url = Column(String(500))
    twitter_url = Column(String(500))
    linkedin_url = Column(String(500))
    youtube_url = Column(String(500))

    instagram_active = Column(Boolean)
    facebook_active = Column(Boolean)
    tiktok_active = Column(Boolean)
    twitter_active = Column(Boolean)
    linkedin_active = Column(Boolean)

    activity_details = Column(JSON, default=dict)
    detected_at = Column(DateTime, default=utcnow)

    lead = relationship("Lead", back_populates="social_media")


class DecisionMaker(Base):
    __tablename__ = "decision_makers"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)

    name = Column(String(255))
    title = Column(String(255))
    linkedin_url = Column(String(500))
    email = Column(String(255))
    source = Column(String(100))
    confidence = Column(Float, default=0.0)

    lead = relationship("Lead", back_populates="decision_makers")


class ContactInfo(Base):
    __tablename__ = "contact_info"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)

    type = Column(String(20))
    value = Column(String(255))
    source = Column(String(100))
    page_url = Column(String(2048))
    confidence = Column(Float, default=0.0)

    lead = relationship("Lead", back_populates="contacts")


class Pitch(Base):
    __tablename__ = "pitches"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)

    gaps_identified = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    pitch_text = Column(Text)
    pitch_subject_line = Column(String(255))
    generated_at = Column(DateTime, default=utcnow)
    edited = Column(Boolean, default=False)

    lead = relationship("Lead", back_populates="pitch")


class AnalysisProgress(Base):
    __tablename__ = "analysis_progress"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)

    overall_status = Column(String(50), default="pending")
    ecommerce_status = Column(String(50), default="pending")
    marketing_status = Column(String(50), default="pending")
    hosting_status = Column(String(50), default="pending")
    ads_status = Column(String(50), default="pending")
    social_status = Column(String(50), default="pending")
    contacts_status = Column(String(50), default="pending")
    decision_makers_status = Column(String(50), default="pending")
    pitch_status = Column(String(50), default="pending")

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_log = Column(JSON, default=list)

    lead = relationship("Lead", back_populates="analysis_progress")
