import json
import math
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6371000.0

GEOJSON_PATHS = [
    Path("data/sensitive_pois.geojson"),
    Path("../data/sensitive_pois.geojson"),
    Path("C:/vs/URBANPULSE/data/sensitive_pois.geojson"),
]

POI_RADII = {
    "school_access": 250.0,
    "hospital_access": 300.0,
    "transit_hub": 250.0,
    "market_arterial": 200.0,
}

LOCATION_SCORES = {
    "low_exposure": 20.0,
    "residential": 40.0,
    "market_arterial": 65.0,
    "transit_hub": 80.0,
    "school_access": 100.0,
    "hospital_access": 100.0,
}

_cached_pois = None


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return EARTH_RADIUS_M * c


def load_pois() -> list[dict[str, Any]]:
    global _cached_pois
    if _cached_pois is not None:
        return _cached_pois

    for path in GEOJSON_PATHS:
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                pois = []
                for feat in data.get("features", []):
                    coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                    props = feat.get("properties", {})
                    pois.append({
                        "name": props.get("name", "Unknown POI"),
                        "poi_type": props.get("poi_type", "school_access"),
                        "lat": coords[1],
                        "lng": coords[0],
                    })
                _cached_pois = pois
                logger.info(f"[Location Risk] Loaded {len(pois)} POIs from {path}")
                return _cached_pois
            except Exception as e:
                logger.warning(f"[Location Risk] Could not parse POIs from {path}: {e}")

    # Fallback built-in POIs for Greater Noida / NCR demo area
    _cached_pois = [
        {"name": "ABC Public School", "poi_type": "school_access", "lat": 28.4506, "lng": 77.5842},
        {"name": "Apollo Clinic", "poi_type": "hospital_access", "lat": 28.4485, "lng": 77.5810},
        {"name": "Knowledge Park Metro Station", "poi_type": "transit_hub", "lat": 28.4590, "lng": 77.5720},
        {"name": "Jagat Farm Central Market", "poi_type": "market_arterial", "lat": 28.4680, "lng": 77.5110},
    ]
    return _cached_pois


def compute_location_risk(
    lat: float | None = None,
    lng: float | None = None,
    location_context: str | None = None,
) -> tuple[float, str, dict[str, Any] | None]:
    """
    Computes Location Risk (L: 0-100) from POI proximity or explicit context string.
    Returns: (L_score, context_key, nearest_poi_dict)
    """
    if location_context and location_context in LOCATION_SCORES:
        return LOCATION_SCORES[location_context], location_context, None

    if lat is None or lng is None:
        return LOCATION_SCORES["low_exposure"], "low_exposure", None

    pois = load_pois()
    matched_contexts: list[tuple[float, str, dict[str, Any]]] = []

    for poi in pois:
        dist_m = haversine_meters(lat, lng, poi["lat"], poi["lng"])
        p_type = poi.get("poi_type", "school_access")
        radius_m = POI_RADII.get(p_type, 250.0)

        if dist_m <= radius_m:
            score = LOCATION_SCORES.get(p_type, 20.0)
            matched_contexts.append((score, p_type, {**poi, "distance_m": round(dist_m, 1)}))

    if not matched_contexts:
        return LOCATION_SCORES["low_exposure"], "low_exposure", None

    # Pick the highest-priority matching sensitive context
    matched_contexts.sort(key=lambda x: x[0], reverse=True)
    best_score, best_ctx, best_poi = matched_contexts[0]
    return best_score, best_ctx, best_poi
