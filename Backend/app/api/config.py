from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.poi import POI
from app.core.shared_config import get_day0_config
from pydantic import BaseModel

router = APIRouter(prefix="/config", tags=["Configuration & Shared Day-0"])


class POIResponse(BaseModel):
    id: str
    name: str
    category: str
    latitude: float
    longitude: float
    buffer_meters: float
    data_source: str

    class Config:
        from_attributes = True


@router.get("/day0", summary="Day-0 Freeze Shared Configuration")
def get_shared_day0_configuration():
    """
    Exposes the Day-0 frozen configuration:
    - 6 locked complaint category keys
    - Configurable department mappings
    - 5-factor priority formula weights (P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E)
    - Sensitive POI types for Location Risk (L)
    """
    return get_day0_config()


@router.get("/pois", response_model=List[POIResponse], summary="List Points of Interest (POIs)")
def list_pois(
    db: Annotated[Session, Depends(get_db)],
    category: Optional[str] = Query(None, description="Filter by POI category (e.g., school, hospital)"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Lists Points of Interest used for spatial indexing and proximity priority boosting.
    """
    query = db.query(POI)
    if category:
        query = query.filter(POI.category == category)
    return query.limit(limit).all()
