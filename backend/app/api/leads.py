import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import (
    ContactInfo,
    DecisionMaker,
    EcommerceData,
    Lead,
    Pitch,
)
from app.core.schemas import (
    LeadBulkCreate,
    LeadCreate,
    LeadDetailResponse,
    LeadResponse,
    StatsResponse,
)

router = APIRouter()


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Lead).where(Lead.domain == data.domain))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Lead for {data.domain} already exists")

    lead = Lead(
        domain=data.domain,
        url=data.url or f"https://{data.domain}",
        company_name=data.company_name,
        source=data.source,
    )
    db.add(lead)
    await db.flush()
    await db.refresh(lead)
    return lead


@router.post("/bulk", response_model=list[LeadResponse], status_code=201)
async def create_leads_bulk(data: LeadBulkCreate, db: AsyncSession = Depends(get_db)):
    created = []
    for raw_domain in data.domains:
        domain = raw_domain.strip().lower()
        for prefix in ("https://", "http://", "www."):
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        domain = domain.rstrip("/")
        if not domain:
            continue

        existing = await db.execute(select(Lead).where(Lead.domain == domain))
        if existing.scalar_one_or_none():
            continue

        lead = Lead(domain=domain, url=f"https://{domain}", source=data.source)
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        created.append(lead)
    return created


@router.post("/upload", response_model=list[LeadResponse], status_code=201)
async def upload_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))

    domains = []
    for row in reader:
        if row:
            domain = row[0].strip().lower()
            for prefix in ("https://", "http://", "www."):
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            domain = domain.rstrip("/")
            if domain and domain != "domain":
                domains.append(domain)

    created = []
    for domain in domains:
        existing = await db.execute(select(Lead).where(Lead.domain == domain))
        if existing.scalar_one_or_none():
            continue
        lead = Lead(domain=domain, url=f"https://{domain}", source="csv_upload")
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        created.append(lead)
    return created


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead)

    if status:
        query = query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)
    if search:
        query = query.where(
            Lead.domain.ilike(f"%{search}%") | Lead.company_name.ilike(f"%{search}%")
        )

    sort_col = getattr(Lead, sort_by, Lead.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Lead.id)))).scalar() or 0
    analyzed = (
        await db.execute(select(func.count(Lead.id)).where(Lead.status == "completed"))
    ).scalar() or 0
    pending = (
        await db.execute(select(func.count(Lead.id)).where(Lead.status == "pending"))
    ).scalar() or 0
    analyzing = (
        await db.execute(select(func.count(Lead.id)).where(Lead.status == "analyzing"))
    ).scalar() or 0
    failed = (
        await db.execute(select(func.count(Lead.id)).where(Lead.status == "failed"))
    ).scalar() or 0

    ecommerce_q = (
        select(func.count(EcommerceData.id)).where(EcommerceData.is_ecommerce.is_(True))
    )
    ecommerce_confirmed = (await db.execute(ecommerce_q)).scalar() or 0

    pitch_count = (await db.execute(select(func.count(Pitch.id)))).scalar() or 0

    return StatsResponse(
        total_leads=total,
        analyzed=analyzed,
        pending=pending,
        analyzing=analyzing,
        failed=failed,
        ecommerce_confirmed=ecommerce_confirmed,
        with_gaps=pitch_count,
    )


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.ecommerce),
            selectinload(Lead.marketing_tools),
            selectinload(Lead.hosting_email),
            selectinload(Lead.ad_activity),
            selectinload(Lead.social_media),
            selectinload(Lead.decision_makers),
            selectinload(Lead.contacts),
            selectinload(Lead.pitch),
        )
    )
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
