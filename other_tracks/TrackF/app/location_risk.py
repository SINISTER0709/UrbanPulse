import json
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "config.json"))
POIS_GEOJSON_PATH = Path(os.getenv("POIS_GEOJSON_PATH", "data/sensitive_pois.geojson"))
ENABLE_OVERPASS_FALLBACK = os.getenv("ENABLE_OVERPASS_FALLBACK", "false").lower() == "true"

# Maps Stage E1 `sensitive_pois.poi_type` values -> config.json location_context keys
POI_TYPE_TO_CONTEXT: dict[str, str] = {
    "school": "school_access",
    "school_access": "school_access",
    "hospital": "hospital_access",
    "hospital_access": "hospital_access",
    "fire_station": "hospital_access",
    "transit_hub": "transit_hub",
    "metro_station": "transit_hub",
    "major_junction": "market_arterial",
    "market_arterial": "market_arterial",
}


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_pois() -> list[dict[str, Any]]:
    if not POIS_GEOJSON_PATH.exists():
        return []
    with POIS_GEOJSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    pois = []
    for feat in data.get("features", []):
        lng, lat = feat["geometry"]["coordinates"]
        props = feat["properties"]
        pois.append({
            "id": props["id"],
            "name": props["name"],
            "poi_type": props["poi_type"],
            "buffer_meters": float(props.get("buffer_meters", 250.0)),
            "lat": float(lat),
            "lng": float(lng),
        })
    return pois


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _query_postgis_pois(lat: float, lng: float) -> list[dict[str, Any]]:
    """Queries Stage E1 `sensitive_pois` table using PostGIS ST_DWithin + per-row buffer_meters."""
    sql = """
        SELECT
            id,
            name,
            poi_type,
            buffer_meters,
            ST_Distance(
                location,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS distance_m
        FROM sensitive_pois
        WHERE ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            buffer_meters
        )
        ORDER BY distance_m ASC
        LIMIT 10;
    """
    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        # PostGIS ST_MakePoint takes (longitude, latitude)
        cur.execute(sql, (lng, lat, lng, lat))
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "poi_type": r[2],
            "buffer_meters": float(r[3]),
            "distance_m": round(float(r[4]), 1),
            "source": "postgis_sensitive_pois",
        }
        for r in rows
    ]


def _query_overpass_sensitive_poi(lat: float, lng: float, radius_m: int = 250) -> dict[str, Any] | None:
    query = f"""
    [out:json][timeout:6];
    (
      node(around:{radius_m},{lat},{lng})["amenity"~"school|hospital|clinic|bus_station"];
      node(around:{radius_m},{lat},{lng})["railway"="station"];
    );
    out body 5;
    """
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=7,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        if not elements:
            return None
        el = elements[0]
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        poi_type = "school" if amenity == "school" else ("hospital" if amenity in {"hospital", "clinic"} else "transit_hub")
        dist = haversine_meters(lat, lng, el["lat"], el["lon"])
        return {
            "name": tags.get("name", "OSM Sensitive POI"),
            "poi_type": poi_type,
            "distance_m": round(dist, 1),
            "source": "osm_overpass",
        }
    except Exception:
        return None


def compute_location_risk(
    lat: float | None = None,
    lng: float | None = None,
    location_context: str | None = None,
) -> dict[str, Any]:
    cfg = load_config()["priority"]
    ctx_scores: dict[str, int] = cfg["location_context_scores"]
    radii: dict[str, float] = cfg["poi_radius_meters"]

    if location_context:
        mapped_ctx = POI_TYPE_TO_CONTEXT.get(location_context, location_context)
        if mapped_ctx in ctx_scores:
            return {
                "score": float(ctx_scores[mapped_ctx]),
                "location_context": mapped_ctx,
                "nearest_poi": None,
                "distance_m": None,
                "source": "explicit_context",
            }

    if lat is None or lng is None:
        return {
            "score": float(ctx_scores["low_exposure"]),
            "location_context": "low_exposure",
            "nearest_poi": None,
            "distance_m": None,
            "source": "default_fallback",
        }

    candidates: list[dict[str, Any]] = []
    if DATABASE_URL:
        try:
            candidates = _query_postgis_pois(lat, lng)
        except Exception:
            candidates = []

    if not candidates:
        for poi in load_pois():
            mapped_ctx = POI_TYPE_TO_CONTEXT.get(poi["poi_type"], "low_exposure")
            max_r = radii.get(mapped_ctx, poi["buffer_meters"])
            dist = haversine_meters(lat, lng, poi["lat"], poi["lng"])
            if dist <= max_r:
                candidates.append({
                    "name": poi["name"],
                    "poi_type": poi["poi_type"],
                    "distance_m": round(dist, 1),
                    "source": "local_poi_geojson",
                })

    best_match = None
    best_score = -1.0
    for hit in candidates:
        mapped_ctx = POI_TYPE_TO_CONTEXT.get(hit["poi_type"], "low_exposure")
        sc = float(ctx_scores.get(mapped_ctx, 40))
        if sc > best_score or (sc == best_score and best_match and hit["distance_m"] < best_match["distance_m"]):
            best_score = sc
            best_match = {
                "score": sc,
                "location_context": mapped_ctx,
                "nearest_poi": hit["name"],
                "distance_m": hit["distance_m"],
                "source": hit["source"],
            }

    if best_match:
        return best_match

    if ENABLE_OVERPASS_FALLBACK:
        osm_hit = _query_overpass_sensitive_poi(lat, lng)
        if osm_hit:
            mapped_ctx = POI_TYPE_TO_CONTEXT.get(osm_hit["poi_type"], "low_exposure")
            return {
                "score": float(ctx_scores.get(mapped_ctx, 40)),
                "location_context": mapped_ctx,
                "nearest_poi": osm_hit["name"],
                "distance_m": osm_hit["distance_m"],
                "source": "osm_overpass",
            }

    return {
        "score": float(ctx_scores["low_exposure"]),
        "location_context": "low_exposure",
        "nearest_poi": None,
        "distance_m": None,
        "source": "no_sensitive_poi_nearby",
    }