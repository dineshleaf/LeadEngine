import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session
from app.core.models import AnalysisProgress, Lead
from app.core.schemas import AnalysisStatusResponse, BulkAnalysisRequest
from app.analyzers.orchestrator import orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_analysis_task(lead_id: int):
    """Background task to run analysis."""
    async with async_session() as db:
        try:
            await orchestrator.run_analysis(lead_id, db)
        except Exception as e:
            logger.error(f"Analysis failed for lead {lead_id}: {e}", exc_info=True)
            try:
                result = await db.execute(select(Lead).where(Lead.id == lead_id))
                lead = result.scalar_one_or_none()
                if lead:
                    lead.status = "failed"
                await db.commit()
            except Exception:
                await db.rollback()


@router.post("/{lead_id}", status_code=202)
async def trigger_analysis(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.status == "analyzing":
        raise HTTPException(status_code=409, detail="Analysis already in progress")

    lead.status = "analyzing"

    # Create progress record immediately so frontend can poll it
    progress_result = await db.execute(
        select(AnalysisProgress).where(AnalysisProgress.lead_id == lead_id)
    )
    progress = progress_result.scalar_one_or_none()
    if not progress:
        progress = AnalysisProgress(lead_id=lead_id)
        db.add(progress)
    progress.overall_status = "pending"
    progress.ecommerce_status = "pending"
    progress.marketing_status = "pending"
    progress.hosting_status = "pending"
    progress.ads_status = "pending"
    progress.social_status = "pending"
    progress.contacts_status = "pending"
    progress.decision_makers_status = "pending"
    progress.pitch_status = "pending"
    progress.started_at = None
    progress.completed_at = None
    progress.error_log = []

    await db.flush()

    background_tasks.add_task(_run_analysis_task, lead_id)

    return {"message": "Analysis started", "lead_id": lead_id}


@router.post("/bulk", status_code=202)
async def trigger_bulk_analysis(
    data: BulkAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    started = []
    for lead_id in data.lead_ids:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if lead and lead.status != "analyzing":
            lead.status = "analyzing"
            background_tasks.add_task(_run_analysis_task, lead_id)
            started.append(lead_id)

    await db.flush()
    return {"message": f"Analysis started for {len(started)} leads", "lead_ids": started}


@router.get("/{lead_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnalysisProgress).where(AnalysisProgress.lead_id == lead_id)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # Check if lead exists
        lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = lead_result.scalar_one_or_none()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return AnalysisStatusResponse(
            lead_id=lead_id,
            overall_status=lead.status,
            modules={},
        )

    return AnalysisStatusResponse(
        lead_id=lead_id,
        overall_status=progress.overall_status,
        modules={
            "ecommerce": progress.ecommerce_status,
            "marketing": progress.marketing_status,
            "hosting": progress.hosting_status,
            "ads": progress.ads_status,
            "social": progress.social_status,
            "contacts": progress.contacts_status,
            "decision_makers": progress.decision_makers_status,
            "pitch": progress.pitch_status,
        },
        started_at=progress.started_at,
        completed_at=progress.completed_at,
    )
