from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import Lead, Pitch
from app.core.schemas import PitchResponse, PitchUpdate
from app.analyzers.pitch_generator import PitchGenerator

router = APIRouter()


@router.post("/{lead_id}", response_model=PitchResponse, status_code=201)
async def generate_pitch(lead_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.ecommerce),
            selectinload(Lead.marketing_tools),
            selectinload(Lead.ad_activity),
            selectinload(Lead.social_media),
            selectinload(Lead.hosting_email),
        )
    )
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis must be completed first")

    # Build analysis data dict from ORM objects
    analysis_data = {"company_name": lead.company_name or lead.domain}

    if lead.ecommerce:
        analysis_data["ecommerce"] = {
            "is_ecommerce": lead.ecommerce.is_ecommerce,
            "platform": lead.ecommerce.platform,
            "confidence_score": lead.ecommerce.confidence_score,
        }
    if lead.marketing_tools:
        mt = lead.marketing_tools
        analysis_data["marketing_tools"] = {
            "has_google_analytics": mt.has_google_analytics,
            "has_gtm": mt.has_gtm,
            "has_gsc": mt.has_gsc,
            "has_facebook_pixel": mt.has_facebook_pixel,
            "has_tiktok_pixel": mt.has_tiktok_pixel,
            "has_clarity": mt.has_clarity,
            "has_hotjar": mt.has_hotjar,
        }
    if lead.ad_activity:
        ad = lead.ad_activity
        analysis_data["ad_activity"] = {
            "is_running_google_ads": ad.is_running_google_ads,
            "is_running_meta_ads": ad.is_running_meta_ads,
            "is_running_tiktok_ads": ad.is_running_tiktok_ads,
        }
    if lead.social_media:
        sm = lead.social_media
        analysis_data["social_media"] = {
            "instagram_url": sm.instagram_url,
            "instagram_active": sm.instagram_active,
            "facebook_url": sm.facebook_url,
            "facebook_active": sm.facebook_active,
            "tiktok_url": sm.tiktok_url,
            "tiktok_active": sm.tiktok_active,
            "linkedin_url": sm.linkedin_url,
        }

    generator = PitchGenerator()
    pitch_data = await generator.analyze(lead.domain, **analysis_data)

    # Save pitch
    existing = await db.execute(select(Pitch).where(Pitch.lead_id == lead_id))
    existing_pitch = existing.scalar_one_or_none()
    if existing_pitch:
        existing_pitch.gaps_identified = pitch_data["gaps_identified"]
        existing_pitch.recommendations = pitch_data["recommendations"]
        existing_pitch.pitch_text = pitch_data["pitch_text"]
        existing_pitch.pitch_subject_line = pitch_data["pitch_subject_line"]
        existing_pitch.edited = False
    else:
        db.add(Pitch(lead_id=lead_id, **pitch_data))

    await db.flush()

    result = await db.execute(select(Pitch).where(Pitch.lead_id == lead_id))
    return result.scalar_one()


@router.get("/{lead_id}", response_model=PitchResponse)
async def get_pitch(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pitch).where(Pitch.lead_id == lead_id))
    pitch = result.scalar_one_or_none()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return pitch


@router.put("/{lead_id}", response_model=PitchResponse)
async def update_pitch(
    lead_id: int, data: PitchUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Pitch).where(Pitch.lead_id == lead_id))
    pitch = result.scalar_one_or_none()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")

    if data.pitch_text is not None:
        pitch.pitch_text = data.pitch_text
    if data.pitch_subject_line is not None:
        pitch.pitch_subject_line = data.pitch_subject_line
    pitch.edited = True

    await db.flush()
    return pitch
