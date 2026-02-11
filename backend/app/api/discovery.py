from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import Lead
from app.core.schemas import (
    DiscoveryImportRequest,
    DiscoveryResult,
    DiscoverySearchRequest,
    LeadResponse,
)
from app.services.search_service import search_google

router = APIRouter()


@router.post("/search", response_model=list[DiscoveryResult])
async def search_domains(data: DiscoverySearchRequest):
    results = await search_google(data.query, data.max_results)
    return [
        DiscoveryResult(
            domain=r["domain"],
            url=r["url"],
            title=r["title"],
            snippet=r["snippet"],
        )
        for r in results
    ]


@router.post("/import", response_model=list[LeadResponse], status_code=201)
async def import_domains(
    data: DiscoveryImportRequest, db: AsyncSession = Depends(get_db)
):
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

        lead = Lead(domain=domain, url=f"https://{domain}", source="discovery")
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        created.append(lead)

    return created
