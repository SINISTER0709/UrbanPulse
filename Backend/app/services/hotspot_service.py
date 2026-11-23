import os
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import numpy as np
from sklearn.cluster import DBSCAN

from app.db.session import SessionLocal
from app.models.incident import Incident
from app.core.shared_config import LOCKED_CATEGORIES

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6371000.0
DBSCAN_EPS_METERS = 400.0
DBSCAN_MIN_SAMPLES = 3

DEMO_HOTSPOTS_PATH = Path("data/demo_hotspot_incidents.json")


def compute_hotspots_and_trends(
    category: str | None = None,
    days: int = 30,
    data_source: str | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """
    Track F Deliverable:
    DBSCAN clustering on distinct incidents + category & area trends.
    Output:
      {"clusters": [{"cluster_id": 1, "distinct_incidents": 12, "centroid": [28.45, 77.58]}],
       "trends": [{"category": "road_damage", "count": 19}]}
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    incidents_data = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        q = db.query(Incident)
        if category:
            q = q.filter(Incident.category == category)
        if data_source:
            q = q.filter(Incident.data_source == data_source)

        all_inc = q.all()
        for inc in all_inc:
            c_time = inc.created_at
            if c_time:
                c_time_utc = c_time if c_time.tzinfo else c_time.replace(tzinfo=timezone.utc)
                if c_time_utc < cutoff:
                    continue
            incidents_data.append({
                "id": inc.id,
                "category": inc.category.value if hasattr(inc.category, "value") else str(inc.category),
                "lat": inc.latitude,
                "lng": inc.longitude,
                "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
                "priority_score": inc.priority_score,
            })
    except Exception as exc:
        logger.warning(f"[Hotspot Service] Database error: {exc}")
    finally:
        if close_session:
            db.close()

    # If database has few records, merge with demo dataset
    if len(incidents_data) < 5 and DEMO_HOTSPOTS_PATH.exists():
        try:
            with DEMO_HOTSPOTS_PATH.open("r", encoding="utf-8") as f:
                demo_items = json.load(f)
            for item in demo_items:
                if category and item.get("category") != category:
                    continue
                incidents_data.append({
                    "id": item.get("id", "demo"),
                    "category": item.get("category", "road_damage"),
                    "lat": item.get("lat", 28.45),
                    "lng": item.get("lng", 77.58),
                    "status": item.get("status", "open"),
                    "priority_score": item.get("priority_score", 50.0),
                })
        except Exception as e:
            logger.warning(f"[Hotspot Service] Could not load demo hotspots: {e}")

    # Compute category trends
    trends_map = {cat: 0 for cat in LOCKED_CATEGORIES}
    for item in incidents_data:
        c = item["category"]
        trends_map[c] = trends_map.get(c, 0) + 1

    trends = [{"category": cat, "count": count} for cat, count in trends_map.items() if count > 0]
    trends.sort(key=lambda t: t["count"], reverse=True)

    # Compute spatial clusters via DBSCAN
    clusters = []
    if len(incidents_data) >= DBSCAN_MIN_SAMPLES:
        coords = np.array([[item["lat"], item["lng"]] for item in incidents_data])
        # Convert degrees to radians for haversine metric
        coords_rad = np.radians(coords)
        eps_rad = DBSCAN_EPS_METERS / EARTH_RADIUS_M

        dbscan = DBSCAN(eps=eps_rad, min_samples=DBSCAN_MIN_SAMPLES, metric="haversine")
        labels = dbscan.fit_predict(coords_rad)

        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:  # Noise
                continue
            cluster_points = coords[labels == label]
            centroid_lat = round(float(np.mean(cluster_points[:, 0])), 5)
            centroid_lng = round(float(np.mean(cluster_points[:, 1])), 5)

            clusters.append({
                "cluster_id": int(label) + 1,
                "distinct_incidents": int(len(cluster_points)),
                "centroid": [centroid_lat, centroid_lng],
                "radius_meters": DBSCAN_EPS_METERS,
            })

    clusters.sort(key=lambda c: c["distinct_incidents"], reverse=True)
    return {
        "days": days,
        "total_distinct_incidents": len(incidents_data),
        "clusters": clusters,
        "trends": trends,
    }
