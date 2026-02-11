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
        await db.flush()

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
        await db.flush()

        errors = []
        analysis_data = {"company_name": lead.company_name or domain}

        # Run analyzers concurrently (grouped for dependency management)
        # Group 1: Independent analyzers
        async def run_ecommerce():
            progress.ecommerce_status = "running"
            await db.flush()
            try:
                data = await self.ecommerce.analyze(domain)
                await self._save_ecommerce(db, lead_id, data)
                progress.ecommerce_status = "completed"
                analysis_data["ecommerce"] = data
            except Exception as e:
                progress.ecommerce_status = "failed"
                errors.append(f"ecommerce: {str(e)}")
                logger.error(f"Ecommerce analysis failed for {domain}: {e}")

        async def run_marketing():
            progress.marketing_status = "running"
            await db.flush()
            try:
                data = await self.marketing.analyze(domain)
                await self._save_marketing(db, lead_id, data)
                progress.marketing_status = "completed"
                analysis_data["marketing_tools"] = data
            except Exception as e:
                progress.marketing_status = "failed"
                errors.append(f"marketing: {str(e)}")
                logger.error(f"Marketing analysis failed for {domain}: {e}")

        async def run_hosting():
            progress.hosting_status = "running"
            await db.flush()
            try:
                data = await self.hosting.analyze(domain)
                await self._save_hosting(db, lead_id, data)
                progress.hosting_status = "completed"
                analysis_data["hosting_email"] = data
            except Exception as e:
                progress.hosting_status = "failed"
                errors.append(f"hosting: {str(e)}")
                logger.error(f"Hosting analysis failed for {domain}: {e}")

        async def run_ads():
            progress.ads_status = "running"
            await db.flush()
            try:
                data = await self.ads.analyze(domain)
                await self._save_ads(db, lead_id, data)
                progress.ads_status = "completed"
                analysis_data["ad_activity"] = data
            except Exception as e:
                progress.ads_status = "failed"
                errors.append(f"ads: {str(e)}")
                logger.error(f"Ad analysis failed for {domain}: {e}")

        async def run_social():
            progress.social_status = "running"
            await db.flush()
            try:
                data = await self.social.analyze(domain)
                await self._save_social(db, lead_id, data)
                progress.social_status = "completed"
                analysis_data["social_media"] = data
            except Exception as e:
                progress.social_status = "failed"
                errors.append(f"social: {str(e)}")
                logger.error(f"Social analysis failed for {domain}: {e}")

        async def run_contacts():
            progress.contacts_status = "running"
            await db.flush()
            try:
                data = await self.contacts.analyze(domain)
                await self._save_contacts(db, lead_id, data)
                progress.contacts_status = "completed"
            except Exception as e:
                progress.contacts_status = "failed"
                errors.append(f"contacts: {str(e)}")
                logger.error(f"Contact analysis failed for {domain}: {e}")

        async def run_decision_makers():
            progress.decision_makers_status = "running"
            await db.flush()
            try:
                data = await self.decision_makers.analyze(domain)
                await self._save_decision_makers(db, lead_id, data)
                progress.decision_makers_status = "completed"
            except Exception as e:
                progress.decision_makers_status = "failed"
                errors.append(f"decision_makers: {str(e)}")
                logger.error(f"Decision maker analysis failed for {domain}: {e}")

        # Run all independent analyzers concurrently
        await asyncio.gather(
            run_ecommerce(),
            run_marketing(),
            run_hosting(),
            run_ads(),
            run_social(),
            run_contacts(),
            run_decision_makers(),
            return_exceptions=True,
        )

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
