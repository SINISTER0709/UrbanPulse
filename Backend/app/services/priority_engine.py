from datetime import datetime, timezone
from typing import Any
import logging

from app.services.location_risk import compute_location_risk
from app.core.shared_config import PRIORITY_WEIGHTS

logger = logging.getLogger(__name__)

SEVERITY_SCORES = {
    "Low": 20.0,
    "Medium": 45.0,
    "High": 75.0,
    "Critical": 100.0,
}

REPORT_COUNT_TIERS = [
    (1, 10.0),
    (3, 30.0),
    (7, 50.0),
    (15, 75.0),
    (999999, 100.0),
]

DAYS_TIERS = [
    (0.999, 0.0),
    (2.999, 25.0),
    (5.999, 50.0),
    (10.0, 75.0),
    (999999, 100.0),
]

ESCALATION_SCORES = {
    "none": 0.0,
    "mild": 30.0,
    "moderate": 60.0,
    "confirmed_worsening": 100.0,
}

CRITICAL_KEYWORDS = [
    "live wire", "electrocution", "sinkhole", "collapsed", "trapped",
    "hospitalized", "rabid", "gas leak", "fire", "manhole cover missing",
    "ambulance", "school gate"
]


def _lookup_tier(value: float, tiers: list[tuple[float, float]]) -> float:
    for threshold, score in tiers:
        if value <= threshold:
            return score
    return tiers[-1][1]


def compute_escalation_factor(
    escalation_level: str | None = None,
    severity_history: list[str] | None = None,
    reopen_count: int = 0,
    worsening_reports: int = 0,
) -> tuple[float, str]:
    if escalation_level and escalation_level in ESCALATION_SCORES:
        return ESCALATION_SCORES[escalation_level], escalation_level

    rank = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    upgraded_steps = 0
    if severity_history and len(severity_history) >= 2:
        start_r = rank.get(severity_history[0], 1)
        end_r = rank.get(severity_history[-1], 1)
        upgraded_steps = max(0, end_r - start_r)

    if upgraded_steps >= 2 or reopen_count >= 2 or worsening_reports >= 2:
        level = "confirmed_worsening"
    elif upgraded_steps == 1 or reopen_count == 1:
        level = "moderate"
    elif worsening_reports == 1:
        level = "mild"
    else:
        level = "none"

    return ESCALATION_SCORES[level], level


def score_from_normalized_factors(
    S: float,
    R: float,
    T: float,
    L: float,
    E: float,
    severity_label: str | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """
    Computes P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E from 0-100 factors.
    """
    w = PRIORITY_WEIGHTS
    for name, val in [("S", S), ("R", R), ("T", T), ("L", L), ("E", E)]:
        if not (0.0 <= val <= 100.0):
            raise ValueError(f"Factor {name} must be between 0 and 100 (got {val}).")

    breakdown = {
        "S": round(w["S"] * S, 1),
        "R": round(w["R"] * R, 1),
        "T": round(w["T"] * T, 1),
        "L": round(w["L"] * L, 1),
        "E": round(w["E"] * E, 1),
    }
    priority_score = round(sum(breakdown.values()), 1)

    urgent_reasons: list[str] = []
    if severity_label == "Critical" or S >= 100.0:
        urgent_reasons.append("critical_severity")
    if priority_score >= 80.0:
        urgent_reasons.append("high_composite_score")
    if text:
        low_text = text.lower()
        matched_kw = [kw for kw in CRITICAL_KEYWORDS if kw in low_text]
        if matched_kw and (severity_label in {"High", "Critical"} or S >= 75.0):
            urgent_reasons.append(f"hazard_keyword:{matched_kw[0]}")

    return {
        "priority_score": priority_score,
        "breakdown": breakdown,
        "raw_factors": {"S": S, "R": R, "T": T, "L": L, "E": E},
        "weights": w,
        "image_evidence_weight": 0.0,
        "urgent_review_flag": len(urgent_reasons) > 0,
        "urgent_reasons": urgent_reasons,
    }


def score_incident(
    severity: str,
    report_count: int = 1,
    unresolved_days: float | None = None,
    created_at: datetime | None = None,
    lat: float | None = None,
    lng: float | None = None,
    location_context: str | None = None,
    escalation_level: str | None = None,
    severity_history: list[str] | None = None,
    reopen_count: int = 0,
    worsening_reports: int = 0,
    text: str | None = None,
) -> dict[str, Any]:
    """
    Computes S, R, T, L (via POI proximity), and E from raw incident metadata.
    """
    # 1. Severity (S)
    sev_cap = severity.capitalize()
    if sev_cap not in SEVERITY_SCORES:
        raise ValueError(f"Invalid severity '{severity}'. Must be Low, Medium, High, or Critical.")
    S = SEVERITY_SCORES[sev_cap]

    # 2. Report Volume (R)
    R = _lookup_tier(float(report_count), REPORT_COUNT_TIERS)

    # 3. Time Unresolved (T)
    if unresolved_days is None:
        if created_at is not None:
            now = datetime.now(timezone.utc)
            c_time = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
            unresolved_days = max(0.0, (now - c_time).total_seconds() / 86400.0)
        else:
            unresolved_days = 0.0
    T = _lookup_tier(float(unresolved_days), DAYS_TIERS)

    # 4. Location Context (L)
    L, matched_ctx, nearest_poi = compute_location_risk(
        lat=lat, lng=lng, location_context=location_context
    )

    # 5. Escalation History (E)
    E, esc_level = compute_escalation_factor(
        escalation_level=escalation_level,
        severity_history=severity_history,
        reopen_count=reopen_count,
        worsening_reports=worsening_reports,
    )

    scored = score_from_normalized_factors(
        S=S, R=R, T=T, L=L, E=E, severity_label=sev_cap, text=text
    )

    # Map composite score to priority tier
    total = scored["priority_score"]
    if scored["urgent_review_flag"] or total >= 75.0:
        priority_label = "critical"
    elif total >= 50.0:
        priority_label = "high"
    elif total >= 30.0:
        priority_label = "medium"
    else:
        priority_label = "low"

    return {
        **scored,
        "priority": priority_label,
        "location_context": matched_ctx,
        "nearest_poi": nearest_poi,
        "escalation_level": esc_level,
        "report_count": report_count,
        "unresolved_days": round(unresolved_days, 2),
    }
