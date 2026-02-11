from fastapi import APIRouter

from app.api.leads import router as leads_router
from app.api.analysis import router as analysis_router
from app.api.discovery import router as discovery_router
from app.api.export import router as export_router
from app.api.pitch import router as pitch_router

api_router = APIRouter()

api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(discovery_router, prefix="/discovery", tags=["discovery"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(pitch_router, prefix="/pitch", tags=["pitch"])
