from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.init_db import init_db, check_postgis
from app.core.shared_config import get_day0_config
from app.api.auth import router as auth_router
from app.api.complaints import router as complaints_router
from app.api.config import router as config_router
from app.api.incidents import router as incidents_router
from app.api.analyze import router as analyze_router
from app.api.evidence import router as evidence_router
from app.api.analytics import router as analytics_router

logger = logging.getLogger("urbanpulse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    Initializes DB tables if database is available.
    """
    if settings.ENVIRONMENT != "testing":
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Database auto-init on startup skipped/failed (will retry when DB starts): {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="UrbanPulse AI Municipal Complaint Analysis & Triage Platform (Track E / Stage E1)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/api/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="api_uploads")

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(complaints_router, prefix=settings.API_V1_STR)
app.include_router(config_router, prefix=settings.API_V1_STR)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(analyze_router, prefix=settings.API_V1_STR)
app.include_router(evidence_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)


@app.get("/api/health", tags=["Health & System"])
def health_check():
    """
    System healthcheck verifying API uptime, database connectivity, and PostGIS status.
    """
    postgis_status = check_postgis()
    day0 = get_day0_config()
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": postgis_status,
        "day0_freeze": day0,
    }
