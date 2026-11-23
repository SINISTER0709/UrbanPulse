import os
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import numpy as np

from app.services.location_risk import haversine_meters
from app.db.session import SessionLocal
from app.models.incident import Incident

logger = logging.getLogger(__name__)

MOCK_INCIDENTS_PATH = Path("data/mock_incidents.json")
MAX_DISTANCE_METERS = 250.0
TIME_WINDOW_DAYS = 14
AUTO_LINK_SIMILARITY = 0.90
ADMIN_REVIEW_SIMILARITY = 0.50

_cached_emb_model = None


def get_embedding_model():
    global _cached_emb_model
    if _cached_emb_model is not None:
        return _cached_emb_model

    try:
        from sentence_transformers import SentenceTransformer
        _cached_emb_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("[Dedup Service] Loaded all-MiniLM-L6-v2 sentence transformer")
        return _cached_emb_model
    except Exception as exc:
        logger.info(f"[Dedup Service] SentenceTransformer not available: {exc}. Using token similarity.")

    return None


def _token_similarity(text1: str, text2: str) -> float:
    def ngrams(text: str, n: int = 3):
        t = re_sub(r"[^\w\s]", "", text.lower())
        words = t.split()
        return set(words) | {t[i:i+n] for i in range(len(t) - n + 1)}

    import re
    re_sub = re.sub
    set1 = ngrams(text1)
    set2 = ngrams(text2)
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / float(len(set1 | set2))


def compute_similarity(text1: str, text2: str) -> float:
    model = get_embedding_model()
    if model is not None:
        try:
            emb = model.encode([text1, text2], normalize_embeddings=True)
            return float(np.dot(emb[0], emb[1]))
        except Exception as e:
            logger.warning(f"[Dedup Service] Embedding compute error: {e}")

    return _token_similarity(text1, text2)


def find_duplicate_candidates(
    text: str,
    category: str,
    lat: float,
    lng: float,
    created_at: datetime | None = None,
    report_id: str | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """
    Track F Deliverable:
    Spatial (<=250m) + category + temporal (<=14d) + text similarity candidate search.
    Output: {"candidates": [{"incident_id": "inc_...", "similarity": 0.89, "distance_m": 35.0, "status": "needs_admin_confirmation"}]}
    """
    now = created_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    cutoff = now - timedelta(days=TIME_WINDOW_DAYS)

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    candidates = []
    try:
        active_incidents = (
            db.query(Incident)
            .filter(
                Incident.category == category,
                Incident.status.notin_(["resolved", "closed"]),
            )
            .all()
        )

        for inc in active_incidents:
            # Check temporal window
            inc_time = inc.created_at
            if inc_time:
                inc_time_utc = inc_time if inc_time.tzinfo else inc_time.replace(tzinfo=timezone.utc)
                if inc_time_utc < cutoff:
                    continue

            # Check distance
            dist_m = haversine_meters(lat, lng, inc.latitude, inc.longitude)
            if dist_m > MAX_DISTANCE_METERS:
                continue

            # Compute semantic text similarity
            sim = round(compute_similarity(text, inc.summary_text), 2)
            if sim >= ADMIN_REVIEW_SIMILARITY:
                status_label = (
                    "auto_linked"
                    if sim >= AUTO_LINK_SIMILARITY
                    else "needs_admin_confirmation"
                )
                candidates.append({
                    "incident_id": inc.id,
                    "similarity": sim,
                    "distance_m": round(dist_m, 1),
                    "status": status_label,
                    "summary_text": inc.summary_text,
                })
    except Exception as exc:
        logger.warning(f"[Dedup Service] DB query error: {exc}")
    finally:
        if close_session:
            db.close()

    # Sort best match first
    candidates.sort(key=lambda c: (c["similarity"], -c["distance_m"]), reverse=True)
    return {
        "report_id": report_id,
        "category": category,
        "candidates": candidates,
    }
