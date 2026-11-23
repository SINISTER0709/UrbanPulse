from datetime import datetime, timezone
from typing import Any

from app.location_risk import compute_location_risk, load_config


def _lookup_tier(value: float, tiers: list[dict[str, Any]], key: str) -> float:
    for tier in tiers:
        if value <= tier[key]:
            return float(tier["score"])
    return float(tiers[-1]["score"])


def compute_escalation_factor(
    escalation_level: str | None = None,
    severity_history: list[str] | None = None,
    reopen_count: int = 0,
    worsening_reports: int = 0,
) -> tuple[float, str]:
    """
    Computes Escalation (E: 0-100) from incident history[cite: 10]:
    - Explicit level ('none'|'mild'|'moderate'|'confirmed_worsening') if supplied, OR
    - Derived deterministically from severity upgrades, reopens, and worsening reports.
    """
    esc_scores: dict[str, int] = load_config()["priority"]["escalation_scores"]

    if escalation_level and escalation_level in esc_scores:
        return float(esc_scores[escalation_level]), escalation_level

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

    return float(esc_scores[level]), level


def score_from_normalized_factors(
    S: float,
    R: float,
    T: float,
    L: float,
    E: float,
    severity_label: str | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """Computes P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E from 0-100 factors."""
    cfg = load_config()["priority"]
    w = cfg["weights"]
    rules = cfg["urgent_review_rules"]

    for name, val in [("S", S), ("R", R), ("T", T), ("L", L), ("E", E)]:
        if not (0.0 <= val <= 100.0):
            raise ValueError(f"Factor {name} must be between 0 and 100 (got {val}).")

    breakdown = {
        "S": round(w["S"] * S, 2),
        "R": round(w["R"] * R, 2),
        "T": round(w["T"] * T, 2),
        "L": round(w["L"] * L, 2),
        "E": round(w["E"] * E, 2),
    }
    priority_score = round(sum(breakdown.values()), 2)

    urgent_reasons: list[str] = []
    if severity_label in rules["flag_on_severities"] or S >= 100.0:
        urgent_reasons.append("critical_severity")
    if priority_score >= rules["flag_on_score_gte"]:
        urgent_reasons.append("high_composite_score")
    if text:
        low_text = text.lower()
        matched_kw = [kw for kw in rules["critical_keywords"] if kw in low_text]
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
    """Full incident-to-priority computation with explainable provenance."""
    cfg = load_config()["priority"]

    if severity not in cfg["severity_scores"]:
        raise ValueError(f"Unsupported severity '{severity}'. Expected Low|Medium|High|Critical.")
    S = float(cfg["severity_scores"][severity])
    R = _lookup_tier(max(1, report_count), cfg["report_count_tiers"], "max_reports")

    if unresolved_days is None:
        if created_at is not None:
            now = datetime.now(timezone.utc)
            dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
            unresolved_days = max(0.0, (now - dt).total_seconds() / 86400.0)
        else:
            unresolved_days = 0.0
    T = _lookup_tier(unresolved_days, cfg["unresolved_days_tiers"], "max_days")

    loc_info = compute_location_risk(lat=lat, lng=lng, location_context=location_context)
    L = loc_info["score"]

    E, esc_label = compute_escalation_factor(
        escalation_level=escalation_level,
        severity_history=severity_history,
        reopen_count=reopen_count,
        worsening_reports=worsening_reports,
    )

    result = score_from_normalized_factors(
        S=S, R=R, T=T, L=L, E=E, severity_label=severity, text=text
    )
    result["context"] = {
        "severity": severity,
        "report_count": report_count,
        "unresolved_days": round(unresolved_days, 2),
        "location": loc_info,
        "escalation_level": esc_label,
    }
    return result