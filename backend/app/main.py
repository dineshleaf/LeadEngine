import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.database import engine
from app.core.models import Base
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ready.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    yield
    await engine.dispose()


app = FastAPI(
    title="LeadEngine",
    description="E-commerce Lead Generation Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins since frontend is served from same origin in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    from app.core.database import async_session
    from sqlalchemy import text
    db_status = "unknown"
    db_type = "unknown"
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            db_status = "connected"
            from app.config import settings
            if "postgresql" in settings.database_url:
                db_type = "postgresql"
            elif "sqlite" in settings.database_url:
                db_type = "sqlite"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Health check DB error: {e}")
    return {"status": "healthy", "service": "LeadEngine", "database": db_status, "db_type": db_type}


# Serve React frontend static files in production
# The Dockerfile builds the frontend into /app/static
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists():
    logger.info(f"Serving frontend from {STATIC_DIR}")

    # Serve static assets (JS, CSS, images)
    if (STATIC_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Serve favicon
    @app.get("/favicon.svg")
    async def favicon():
        favicon_path = STATIC_DIR / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(favicon_path)

    # Catch-all: serve index.html for client-side routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return {"detail": "Not found"}
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
else:
    logger.info("No static directory found — running API only (dev mode)")
