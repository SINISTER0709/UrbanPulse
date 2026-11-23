import json
import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from app.location_risk import haversine_meters, load_config

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
MOCK_INCIDENTS_PATH = Path(os.getenv("MOCK_INCIDENTS_PATH", "data/mock_incidents.json"))


@lru_cache(maxsize=2)
def get_embedding_model(model_name: str | None = None) -> SentenceTransformer:
    name = model_name or load_config()["deduplication"]["embedding_model"]
    return SentenceTransformer(name)


def _parse_iso(ts: str | datetime) -> datetime:
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _fetch_candidates_postgis(
    category: str,
    lat: float,
    lng: float,
    created_at: datetime,
    max_distance_m: float,
    time_window_days: int,
) -> list[dict[str, Any]]:
    """Queries Stage E1 `incidents` table with spatial + category + temporal pre-filters."""
    sql = """
        SELECT
            id,
            category,
            summary_text,
            ST_Y(location::geometry) AS lat,
            ST_X(location::geometry) AS lng,
            ST_Distance(
                location,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS distance_m,
            status,
            created_at
        FROM incidents
        WHERE category = %s
          AND status NOT IN ('resolved', 'closed')
          AND created_at >= %s - (%s * INTERVAL '1 day')
          AND created_at <= %s + INTERVAL '1 day'
          AND ST_DWithin(
                location,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
              )
        ORDER BY distance_m ASC
        LIMIT 50;
    """
    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(
            sql,
            (
                lng, lat,
                category,
                created_at, time_window_days,
                created_at,
                lng, lat, max_distance_m,
            ),
        )
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "category": r[1],
            "summary_text": r[2],
            "lat": float(r[3]),
            "lng": float(r[4]),
            "distance_m": round(float(r[5]), 1),
            "incident_status": r[6],
            "created_at": r[7].isoformat(),
        }
        for r in rows
    ]


def _fetch_candidates_local(
    category: str,
    lat: float,
    lng: float,
    created_at: datetime,
    max_distance_m: float,
    time_window_days: int,
) -> list[dict[str, Any]]:
    """Local JSON equivalent of the Stage E1 PostGIS query for standalone testing."""
    if not MOCK_INCIDENTS_PATH.exists():
        return []
    with MOCK_INCIDENTS_PATH.open("r", encoding="utf-8") as f:
        incidents = json.load(f)

    min_dt = created_at - timedelta(days=time_window_days)
    max_dt = created_at + timedelta(days=1)
    hits = []

    for inc in incidents:
        if inc.get("category") != category:
            continue
        if inc.get("status", "open") in {"resolved", "closed"}:
            continue
        inc_dt = _parse_iso(inc["created_at"])
        if not (min_dt <= inc_dt <= max_dt):
            continue
        dist = haversine_meters(lat, lng, float(inc["lat"]), float(inc["lng"]))
        if dist > max_distance_m:
            continue
        hits.append({
            "id": inc["id"],
            "category": inc["category"],
            "summary_text": inc["summary_text"],
            "lat": float(inc["lat"]),
            "lng": float(inc["lng"]),
            "distance_m": round(dist, 1),
            "incident_status": inc.get("status", "open"),
            "created_at": inc["created_at"],
        })

    hits.sort(key=lambda x: x["distance_m"])
    return hits[:50]


def find_duplicate_candidates(
    text: str,
    category: str,
    lat: float,
    lng: float,
    created_at: datetime | str | None = None,
    report_id: str | None = None,
) -> dict[str, Any]:
    cfg = load_config()["deduplication"]
    max_dist = float(cfg["max_distance_meters"])
    window_days = int(cfg["time_window_days"])
    auto_sim = float(cfg["auto_link_similarity"])
    review_sim = float(cfg["admin_review_similarity"])

    ref_dt = _parse_iso(created_at) if created_at else datetime.now(timezone.utc)

    source_used = "local_mock_json"
    if DATABASE_URL:
        try:
            raw_candidates = _fetch_candidates_postgis(
                category, lat, lng, ref_dt, max_dist, window_days
            )
            source_used = "postgis_incidents"
        except Exception:
            raw_candidates = _fetch_candidates_local(
                category, lat, lng, ref_dt, max_dist, window_days
            )
    else:
        raw_candidates = _fetch_candidates_local(
            category, lat, lng, ref_dt, max_dist, window_days
        )

    if not raw_candidates:
        return {
            "report_id": report_id,
            "candidates": [],
            "data_backend": source_used,
        }

    model = get_embedding_model()
    texts = [text.strip()] + [c["summary_text"] for c in raw_candidates]
    embeddings = model.encode(texts, normalize_embeddings=True)
    query_vec = embeddings[0]
    cand_vecs = embeddings[1:]
    sims = np.dot(cand_vecs, query_vec)

    matched = []
    for cand, sim in zip(raw_candidates, sims):
        sim_val = round(float(sim), 4)
        if sim_val < review_sim:
            continue
        match_status = (
            "high_confidence_match" if sim_val >= auto_sim else "needs_admin_confirmation"
        )
        matched.append({
            "incident_id": cand["id"],
            "similarity": sim_val,
            "distance_m": cand["distance_m"],
            "status": match_status,
            "summary_text": cand["summary_text"],
            "created_at": cand["created_at"],
        })

    matched.sort(key=lambda x: (-x["similarity"], x["distance_m"]))
    return {
        "report_id": report_id,
        "candidates": matched,
        "data_backend": source_used,
    }