import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, synonym
from app.models.base import Base, SpatialPoint


def generate_poi_id() -> str:
    return f"poi_{uuid.uuid4().hex[:10]}"


class POI(Base):
    """
    Points of Interest (critical infrastructure, hospitals, schools, transit junctions)
    Used for spatial proximity indexing and priority escalation calculations.
    Table named 'sensitive_pois' per specification.
    """
    __tablename__ = "sensitive_pois"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_poi_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Exact column name 'poi_type' with 'category' synonym for seamless query drop-in
    poi_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category = synonym("poi_type")

    # Data source tag
    data_source: Mapped[str] = mapped_column(String(64), default="osm_overpass", nullable=False, index=True)

    # Spatial Point with GIST index in PostGIS
    location = mapped_column(SpatialPoint, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    buffer_meters: Mapped[float] = mapped_column(Float, default=200.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_sensitive_pois_coords", "latitude", "longitude"),
        Index("idx_sensitive_pois_type_datasource", "poi_type", "data_source"),
    )
