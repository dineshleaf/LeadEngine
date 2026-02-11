from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.export_service import export_csv, export_excel

router = APIRouter()


@router.get("/csv")
async def download_csv(
    lead_ids: Optional[str] = Query(None, description="Comma-separated lead IDs"),
    db: AsyncSession = Depends(get_db),
):
    ids = None
    if lead_ids:
        ids = [int(x.strip()) for x in lead_ids.split(",") if x.strip().isdigit()]

    content = await export_csv(db, ids)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


@router.get("/excel")
async def download_excel(
    lead_ids: Optional[str] = Query(None, description="Comma-separated lead IDs"),
    db: AsyncSession = Depends(get_db),
):
    ids = None
    if lead_ids:
        ids = [int(x.strip()) for x in lead_ids.split(",") if x.strip().isdigit()]

    content = await export_excel(db, ids)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads_export.xlsx"},
    )
