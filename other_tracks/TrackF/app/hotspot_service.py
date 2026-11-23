import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from shapely.geometry import Point
from sklearn.cluster import DBSCAN

from app.location_risk import load_config

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DEMO_HOTSPOTS_PATH = Path(
    os.getenv("DEMO_HOTSPOTS_PATH", "data/demo_hotspot_incidents.json")
)
EARTH_RADIUS_M = 6371000.0


def _parse_iso(ts: str | datetime) -> datetime:
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _load_incidents_postgis(
    category: str | None,
    days: int,
    data_source: str | None,
) -> list[dict[str, Any]]:
    """Loads distinct incidents from Stage E1 `incidents` table."""
    clauses = ["created_at >= NOW() - (%s * INTERVAL '1 day')"]
    params: list[Any] = [days]

    if category:
        clauses.append("category = %s")
        params.append(category)
    if data_source:
        clauses.append("data_source = %s")
        params.append(data_source)

    sql = f"""
        SELECT
            id,
            category,
            summary_text,
            ST_Y(location::geometry) AS lat,
            ST_X(location::geometry) AS lng,
            status,
            priority,
            data_source,
            created_at
        FROM incidents
        WHERE {' AND '.join(clauses)}
        ORDER BY created_at DESC;
    """
    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "category": r[1],
            "summary_text": r[2],
            "lat": float(r[3]),
            "lng": float(r[4]),
            "status": r[5],
            "priority": r[6],
            "data_source": r[7],
            "created_at": r[8].isoformat(),
        }
        for r in rows
    ]


def _load_incidents_local(
    category: str | None,
    days: int,
    data_source: str | None,
) -> list[dict[str, Any]]:
    if not DEMO_HOTSPOTS_PATH.exists():
        return []
    with DEMO_HOTSPOTS_PATH.open("r", encoding="utf-8") as f:
        records = json.load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = []
    for rec in records:
        if category and rec.get("category") != category:
            continue
        if data_source and rec.get("data_source") != data_source:
            continue
        if _parse_iso(rec["created_at"]) < cutoff:
            continue
        filtered.append(rec)
    return filtered


def compute_hotspots_and_trends(
    category: str | None = None,
    days: int = 30,
    data_source: str | None = None,
    eps_meters: float | None = None,
    min_samples: int | None = None,
) -> dict[str, Any]:
    cfg = load_config()["hotspots"]
    eps_m = float(eps_meters or cfg["dbscan_eps_meters"])
    min_pts = int(min_samples or cfg["dbscan_min_samples"])

    backend = "local_demo_json"
    if DATABASE_URL:
        try:
            rows = _load_incidents_postgis(category, days, data_source)
            backend = "postgis_incidents"
        except Exception:
            rows = _load_incidents_local(category, days, data_source)
    else:
        rows = _load_incidents_local(category, days, data_source)

    if not rows:
        return {
            "clusters": [],
            "trends": [],
            "total_distinct_incidents": 0,
            "noise_incidents": 0,
            "data_backend": backend,
        }

    # Deduplicate strictly by incident ID so raw duplicate reports never inflate hotspots
    df = pd.DataFrame(rows).drop_duplicates(subset=["id"]).reset_index(drop=True)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(lng, lat) for lng, lat in zip(df["lng"], df["lat"])],
        crs="EPSG:4326",
    )

    coords_rad = np.radians(gdf[["lat", "lng"]].values)
    eps_rad = eps_m / EARTH_RADIUS_M
    labels = DBSCAN(eps=eps_rad, min_samples=min_pts, metric="haversine").fit_predict(
        coords_rad
    )
    gdf["cluster_id"] = labels

    clusters = []
    for cid in sorted(c for c in set(labels) if c != -1):
        sub = gdf[gdf["cluster_id"] == cid]
        centroid_lat = round(float(sub["lat"].mean()), 6)
        centroid_lng = round(float(sub["lng"].mean()), 6)
        hull = sub.geometry.unary_union.convex_hull
        top_cat = sub["category"].mode().iloc[0]

        clusters.append({
            "cluster_id": int(cid) + 1,
            "distinct_incidents": int(len(sub)),
            "centroid": [centroid_lat, centroid_lng],
            "dominant_category": top_cat,
            "category_counts": {k: int(v) for k, v in sub["category"].value_counts().items()},
            "incident_ids": sub["id"].tolist(),
            "hull_geojson": hull.__geo_interface__,
        })

    clusters.sort(key=lambda x: x["distinct_incidents"], reverse=True)

    trends = [
        {"category": cat, "count": int(cnt)}
        for cat, cnt in gdf["category"].value_counts().items()
    ]

    return {
        "clusters": clusters,
        "trends": trends,
        "total_distinct_incidents": int(len(gdf)),
        "noise_incidents": int((gdf["cluster_id"] == -1).sum()),
        "params": {"eps_meters": eps_m, "min_samples": min_pts, "days": days},
        "data_backend": backend,
    }