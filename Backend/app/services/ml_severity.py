import os
import re
import logging
from pathlib import Path
from typing import Any
import joblib
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_PATHS = [
    Path("models/severity_pipeline_v2.joblib"),
    Path("severity_pipeline_v2.joblib"),
    Path("../models/severity_pipeline_v2.joblib"),
    Path("C:/vs/URBANPULSE/models/severity_pipeline_v2.joblib"),
]

CRIT_KEYWORDS = {
    "sinkhole", "collapsed", "electrocution", "live wire", "sparking", "fire",
    "gas leak", "trapped", "danger", "urgent", "ambulance", "death", "injury",
    "emergency", "explosion", "manhole cover missing", "rabid"
}

HIGH_KEYWORDS = {
    "pothole", "traffic", "school", "hospital", "burst", "overflowing", "broken",
    "choked", "accident", "deep", "major", "risk", "flooding", "blackout"
}

LOW_KEYWORDS = {
    "flickering", "delay", "small", "minor", "cleaning", "noise", "dust", "faded",
    "paint", "park", "bench", "litter"
}

_cached_pipeline = None


def get_pipeline():
    global _cached_pipeline
    if _cached_pipeline is not None:
        return _cached_pipeline

    for path in MODEL_PATHS:
        if path.exists():
            try:
                _cached_pipeline = joblib.load(str(path))
                logger.info(f"[ML Severity] Loaded severity model from {path}")
                return _cached_pipeline
            except Exception as e:
                logger.warning(f"[ML Severity] Could not unpickle model from {path}: {e}")

    return None


def clean_text_fn(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def extract_features(text: str) -> pd.DataFrame:
    clean = clean_text_fn(text)
    words = set(clean.split())
    word_count = len(clean.split())

    crit_hits = sum(1 for kw in CRIT_KEYWORDS if kw in clean)
    high_hits = sum(1 for kw in HIGH_KEYWORDS if kw in clean)
    low_hits = sum(1 for kw in LOW_KEYWORDS if kw in clean)

    return pd.DataFrame([{
        "clean_text": clean,
        "crit_hits": crit_hits,
        "high_hits": high_hits,
        "low_hits": low_hits,
        "word_count": word_count,
    }])


def estimate_severity_text(text: str, submitted_at: str | None = None) -> dict[str, Any]:
    """
    Track B Deliverable:
    Predicts severity from complaint text and permitted submission-time features (never image results).
    Returns: {"severity": "High", "model_confidence": 0.86}
    """
    pipeline = get_pipeline()
    if pipeline is not None:
        try:
            df = extract_features(text)
            pred = pipeline.predict(df)[0]
            probs = pipeline.predict_proba(df)[0]
            confidence = round(float(max(probs)), 2)

            # Ensure valid capitalisation
            sev_str = str(pred).capitalize()
            if sev_str in ("Low", "Medium", "High", "Critical"):
                return {
                    "severity": sev_str,
                    "model_confidence": confidence,
                    "model_used": "joblib_v2"
                }
        except Exception as exc:
            logger.warning(f"[ML Severity] Pipeline predict error: {exc}. Using rule fallback.")

    # Rule-based fallback if ML pipeline is missing or fails
    clean = text.lower()
    if any(k in clean for k in CRIT_KEYWORDS):
        return {"severity": "Critical", "model_confidence": 0.90, "model_used": "rule_fallback"}
    if any(k in clean for k in HIGH_KEYWORDS):
        return {"severity": "High", "model_confidence": 0.75, "model_used": "rule_fallback"}
    if any(k in clean for k in LOW_KEYWORDS):
        return {"severity": "Low", "model_confidence": 0.70, "model_used": "rule_fallback"}

    return {"severity": "Medium", "model_confidence": 0.60, "model_used": "rule_fallback"}
