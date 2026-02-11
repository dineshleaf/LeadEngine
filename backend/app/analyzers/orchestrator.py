import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    AdActivityData,
    AnalysisProgress,
    ContactInfo,
    DecisionMaker,
    EcommerceData,
    HostingEmailData,
    Lead,
    MarketingToolsData,
    Pitch,
    SocialMediaData,
)
from app.analyzers.ecommerce_detector import EcommerceDetector
from app.analyzers.marketing_tools import MarketingToolsAnalyzer
from app.analyzers.hosting_email import HostingEmailAnalyzer
from app.analyzers.ad_activity import AdActivityAnalyzer
from app.analyzers.social_media import SocialMediaAnalyzer
from app.analyzers.decision_makers import DecisionMakerAnalyzer
from app.analyzers.contact_info import ContactInfoAnalyzer
from app.analyzers.pitch_generator import PitchGenerator

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    def __init__(self):
        self.ecommerce = EcommerceDetector()
        self.marketing = MarketingToolsAnalyzer()
        self.hosting = HostingEmailAnalyzer()
        self.ads = AdActivityAnalyzer()
        self.social = SocialMediaAnalyzer()
        self.decision_makers = DecisionMakerAnalyzer()
        self.contacts = ContactInfoAnalyzer()
        self.pitch_gen = PitchGenerator()

    async def run_analysis(self, lead_id: int, db: AsyncSession):
        # Get the lead
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return

        domain = lead.domain
        lead.status = "analyzing"

        # Create or reset progress tracking
        progress_result = await db.execute(
            select(AnalysisProgress).where(AnalysisProgress.lead_id == lead_id)
        )
        progress = progress_result.scalar_one_or_none()
        if not progress:
            progress = AnalysisProgress(lead_id=lead_id)
            db.add(progress)

        progress.overall_status = "running"
        progress.started_at = datetime.utcnow()
        progress.error_log = []

        # Mark all modules as running
        progress.ecommerce_status = "running"
        progress.marketing_status = "running"
        progress.hosting_status = "running"
        progress.ads_status = "running"
        progress.social_status = "running"
        progress.contacts_status = "running"
        progress.decision_makers_status = "running"
        await db.flush()
        await db.commit()

        errors = []
        analysis_data = {"company_name": lead.company_name or domain}

        # Run all HTTP analyses concurrently (no DB operations here)
        async def safe_analyze(name, analyzer):
            try:
                return await analyzer.analyze(domain)
            except Exception as e:
                logger.error(f"{name} analysis failed for {domain}: {e}")
                return e

        results = await asyncio.gather(
            safe_analyze("ecommerce", self.ecommerce),
            safe_analyze("marketing", self.marketing),
            safe_analyze("hosting", self.hosting),
            safe_analyze("ads", self.ads),
            safe_analyze("social", self.social),
            safe_analyze("contacts", self.contacts),
            safe_analyze("decision_makers", self.decision_makers),
        )

        module_names = [
            "ecommerce", "marketing", "hosting",
            "ads", "social", "contacts", "decision_makers",
        ]
        save_fns = [
            self._save_ecommerce, self._save_marketing, self._save_hosting,
            self._save_ads, self._save_social, self._save_contacts,
            self._save_decision_makers,
        ]
        status_fields = [
            "ecommerce_status", "marketing_status", "hosting_status",
            "ads_status", "social_status", "contacts_status",
            "decision_makers_status",
        ]
        data_keys = [
            "ecommerce", "marketing_tools", "hosting_email",
            "ad_activity", "social_media", None, None,
        ]

        # Save results sequentially (safe for single DB session)
        for i, (name, data) in enumerate(zip(module_names, results)):
            if isinstance(data, Exception):
                setattr(progress, status_fields[i], "failed")
                errors.append(f"{name}: {str(data)}")
            else:
                try:
                    await save_fns[i](db, lead_id, data)
                    setattr(progress, status_fields[i], "completed")
                    if data_keys[i]:
                        analysis_data[data_keys[i]] = data
                except Exception as e:
                    setattr(progress, status_fields[i], "failed")
                    errors.append(f"{name}: {str(e)}")
                    logger.error(f"{name} save failed for {domain}: {e}")
            await db.flush()

        # Run pitch generator (depends on other results)
        progress.pitch_status = "running"
        await db.flush()
        try:
            pitch_data = await self.pitch_gen.analyze(domain, **analysis_data)
            await self._save_pitch(db, lead_id, pitch_data)
            progress.pitch_status = "completed"
        except Exception as e:
            progress.pitch_status = "failed"
            errors.append(f"pitch: {str(e)}")
            logger.error(f"Pitch generation failed for {domain}: {e}")

        # Finalize
        progress.error_log = errors
        progress.completed_at = datetime.utcnow()

        if errors:
            if len(errors) >= 7:
                lead.status = "failed"
                progress.overall_status = "failed"
            else:
                lead.status = "completed"
                progress.overall_status = "partial_failure"
        else:
            lead.status = "completed"
            progress.overall_status = "completed"

        await db.flush()
        await db.commit()

    async def _save_ecommerce(self, db: AsyncSession, lead_id: int, data: dict):
        existing = await db.execute(
            select(EcommerceData).where(EcommerceData.lead_id == lead_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            db.add(EcommerceData(lead_id=lead_id, **data))
        await db.flush()

    async def _save_marketing(self, db: AsyncSession, lead_id: int, data: dict):
        existing = await db.execute(
            select(MarketingToolsData).where(MarketingToolsData.lead_id == lead_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            db.add(MarketingToolsData(lead_id=lead_id, **data))
        await db.flush()

    async def _save_hosting(self, db: AsyncSession, lead_id: int, data: dict):
        existing = await db.execute(
            select(HostingEmailData).where(HostingEmailData.lead_id == lead_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            db.add(HostingEmailData(lead_id=lead_id, **data))
        await db.flush()

    async def _save_ads(self, db: AsyncSession, lead_id: int, data: dict):
        existing = await db.execute(
            select(AdActivityData).where(AdActivityData.lead_id == lead_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            db.add(AdActivityData(lead_id=lead_id, **data))
        await db.flush()

    async def _save_social(self, db: AsyncSession, lead_id: int, data: dict):
        existing = await db.execute(
            select(SocialMediaData).where(SocialMediaData.lead_id == lead_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            db.add(SocialMediaData(lead_id=lead_id, **data))
        await db.flush()

    async def _save_contacts(self, db: AsyncSession, lead_id: int, data: dict):
        # Delete existing contacts and add new ones
        existing = await db.execute(
            select(ContactInfo).where(ContactInfo.lead_id == lead_id)
        )
        for obj in existing.scalars().all():
            await db.delete(obj)

        for contact in data.get("contacts", []):
            db.add(ContactInfo(lead_id=lead_id, **contact))
        await db.flush()

    async def _save_decision_makers(self, db: AsyncSession, lead_id: int, data: dict):
        # Delete existing and add new ones
        existing = await db.execute(
            select(DecisionMaker).where(DecisionMaker.lead_id == lead_id)
        )
        for obj in existing.scalars().all():
            await db.delete(obj)

        for person in data.get("decision_makers", []):
            db.add(DecisionMaker(lead_id=lead_id, **person))
        await db.flush()

    async def _save_pitch(self, db: AsyncSession, lead_id: int, data: dict):
        existing = await db.execute(
            select(Pitch).where(Pitch.lead_id == lead_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            db.add(Pitch(lead_id=lead_id, **data))
        await db.flush()


orchestrator = AnalysisOrchestrator()
