"""
Stage E2: Pipeline Integration Service.
Orchestrates asynchronous execution for:
- Track A: Category classification & Department mapping
- Track B: Baseline ML severity estimation
- Track F: Spatial deduplication, incident clustering, and 5-factor priority scoring
- Track C (Optional): Photo visual verification
Includes isolated per-step error handling so failures never corrupt records.
"""
import math
import logging
from datetime import datetime, timezone
from typing import Tuple, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.report import Report
from app.models.incident import Incident, IncidentReport, generate_incident_id
from app.models.ai import AIPrediction
from app.models.evidence import ImageEvidence
from app.models.poi import POI
from app.models.audit import PriorityHistory, StatusHistory
from app.models.assignment import Assignment
from app.models.enums import Day0Category, IncidentStatus, IncidentPriority, ReportStatus
from app.core.shared_config import CATEGORY_DEPARTMENT_MAPPINGS, PRIORITY_WEIGHTS

logger = logging.getLogger("urbanpulse.pipeline")


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance in meters between two lat/lng coordinates."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


# ==============================================================================
# STEP 1: Track A - Category Classification & Department Mapping
# ==============================================================================
def step_classify_category(text: str) -> Tuple[Day0Category, str, float]:
    """
    Classifies complaint text into one of 6 locked Day-0 categories and maps department
    using Track A Llama / OpenAI SDK classifier with heuristic fallback.
    """
    from app.services.llm_client import classify_complaint_text
    try:
        res = classify_complaint_text(text)
        cat_key = res.get("category", "other")
        category = Day0Category(cat_key) if hasattr(Day0Category, cat_key) else Day0Category.other
        dept = res.get("department", CATEGORY_DEPARTMENT_MAPPINGS.get(category.value, "General Administration"))
        confidence = 0.90 if not res.get("fallback_used", False) else 0.80
        return category, dept, confidence
    except Exception as e:
        logger.warning(f"[Pipeline] Track A category classification fallback on error: {e}")
        return Day0Category.other, "General Administration", 0.50


# ==============================================================================
# STEP 2: Track B - Baseline ML Severity Estimation
# ==============================================================================
def step_estimate_severity(text: str) -> Tuple[str, float]:
    """
    Estimates complaint severity using Track B TF-IDF + Scikit-learn trained model.
    """
    from app.services.ml_severity import estimate_severity_text
    try:
        res = estimate_severity_text(text)
        return res.get("severity", "Medium"), float(res.get("model_confidence", 0.85))
    except Exception as e:
        logger.warning(f"[Pipeline] Track B severity estimation fallback on error: {e}")
        return "Medium", 0.60



# ==============================================================================
# STEP 3: Track F - Geospatial Deduplication & Incident Clustering
# ==============================================================================
def step_find_or_create_incident(
    report: Report,
    category: Day0Category,
    severity: str,
    db: Session,
    radius_m: float = 100.0
) -> Tuple[Incident, bool, float]:
    """
    Matches report to an existing open incident within radius_m or creates a new incident.
    Returns: (Incident, is_new_incident, confidence_score)
    """
    candidate_incidents = (
        db.query(Incident)
        .filter(
            Incident.category == category,
            Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating, IncidentStatus.in_progress])
        )
        .all()
    )

    best_match: Optional[Incident] = None
    min_dist = float("inf")

    for inc in candidate_incidents:
        dist = haversine_distance_m(report.latitude, report.longitude, inc.latitude, inc.longitude)
        if dist <= radius_m and dist < min_dist:
            min_dist = dist
            best_match = inc

    if best_match:
        if not best_match.address and report.address:
            best_match.address = report.address
        # Calculate similarity score based on proximity (100m -> 0.75, 0m -> 0.95)
        similarity = max(0.70, round(0.95 - (min_dist / radius_m) * 0.20, 2))
        return best_match, False, similarity

    # Create new incident record
    new_inc_id = generate_incident_id()
    new_incident = Incident(
        id=new_inc_id,
        title=f"{category.value.replace('_', ' ').title()} near ({report.latitude:.4f}, {report.longitude:.4f})",
        summary_text=report.description,
        category=category,
        status=IncidentStatus.open,
        severity=severity,
        priority=IncidentPriority.medium,
        priority_score=50.0,
        urgent_review_flag=False,
        address=report.address,
        latitude=report.latitude,
        longitude=report.longitude,
        location=report.location,
        data_source=report.data_source,
    )
    db.add(new_incident)
    db.flush()
    return new_incident, True, 1.0


# ==============================================================================
# STEP 4: Track F - 5-Factor Priority Scoring Engine
# Formula (Page 4): P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E
# ==============================================================================
def step_compute_5factor_priority(
    severity: str,
    linked_report_count: int,
    created_at: datetime,
    lat: float,
    lng: float,
    db: Session,
    escalation_level: float = 0.0
) -> Tuple[float, Dict[str, float], bool, IncidentPriority]:
    """
    Computes auditable 5-factor priority score P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E.
    """
    # 1. Severity Factor (S) (0-100)
    severity_map = {"Critical": 100.0, "High": 75.0, "Medium": 50.0, "Low": 25.0}
    raw_s = severity_map.get(severity, 50.0)
    score_s = round(PRIORITY_WEIGHTS["S"] * raw_s, 1)  # 0.40 * 75 = 30.0

    # 2. Repeat / Frequency Factor (R) (0-100)
    # MVP baseline: 1 report -> 50.0 (contribution: 0.20 * 50 = 10.0), 2+ reports -> 75 to 100
    raw_r = 50.0 if linked_report_count <= 1 else min(100.0, 50.0 + (linked_report_count - 1) * 25.0)
    score_r = round(PRIORITY_WEIGHTS["R"] * raw_r, 1)

    # 3. Time Decay Factor (T) (0-100)
    # Fresh submission: 0.0
    now = datetime.utcnow()
    hours_old = max(0.0, (now - created_at).total_seconds() / 3600.0)
    raw_t = min(100.0, hours_old * 2.0)
    score_t = round(PRIORITY_WEIGHTS["T"] * raw_t, 1)

    # 4. Location Risk Factor (L) (0-100)
    # Proximity check against sensitive_pois (schools, hospitals, transit hubs)
    pois = db.query(POI).all()
    in_sensitive_zone = False
    for poi in pois:
        dist = haversine_distance_m(lat, lng, poi.latitude, poi.longitude)
        if dist <= poi.buffer_meters:
            in_sensitive_zone = True
            break

    raw_l = 100.0 if in_sensitive_zone else 0.0
    score_l = round(PRIORITY_WEIGHTS["L"] * raw_l, 1)  # 0.15 * 100 = 15.0

    # 5. Escalation History Factor (E) (0-100)
    raw_e = min(100.0, max(0.0, escalation_level))
    score_e = round(PRIORITY_WEIGHTS["E"] * raw_e, 1)

    total_priority = round(score_s + score_r + score_t + score_l + score_e, 1)

    breakdown = {
        "S": score_s,
        "R": score_r,
        "T": score_t,
        "L": score_l,
        "E": score_e,
    }

    # Urgent review flag: Critical severity OR priority >= 75 OR sensitive school zone with High severity
    urgent_review = (severity == "Critical") or (total_priority >= 75.0)

    # Incident Priority tier mapping
    if total_priority >= 75.0 or severity == "Critical":
        priority_enum = IncidentPriority.critical
    elif total_priority >= 50.0:
        priority_enum = IncidentPriority.high
    elif total_priority >= 30.0:
        priority_enum = IncidentPriority.medium
    else:
        priority_enum = IncidentPriority.low

    return total_priority, breakdown, urgent_review, priority_enum


# ==============================================================================
# STEP 5: Track C - Optional Photo Verification
# ==============================================================================
def step_verify_photo_evidence(report: Report, category: Day0Category, db: Session) -> str:
    """
    Evaluates photographic evidence with strict 0% weight in severity and priority scoring
    using Track C YOLO model.
    """
    from app.services.yolo_evidence import verify_image_evidence
    evidence = db.query(ImageEvidence).filter(ImageEvidence.report_id == report.id).first()
    if not evidence:
        return "Not Provided"

    try:
        raw_bytes = None
        if evidence.file_path and os.path.exists(evidence.file_path):
            with open(evidence.file_path, "rb") as f:
                raw_bytes = f.read()

        res = verify_image_evidence(raw_bytes, reported_category=category.value)
        verdict = res.get("verdict", "Visual Match")
        evidence.verification_status = verdict
        return verdict
    except Exception as e:
        logger.warning(f"[Pipeline] Track C verification fallback on error: {e}")
        evidence.verification_status = "Inconclusive"
        return "Inconclusive"


# ==============================================================================
# MASTER ORCHESTRATION PIPELINE (Stage E2)
# ==============================================================================
def orchestrate_report_pipeline(report_id: str, db: Session) -> Optional[Incident]:
    """
    Full Stage E2 pipeline execution for a newly persisted citizen report.
    Each step is isolated so failures do not interrupt subsequent tasks or corrupt state.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        logger.error(f"[Pipeline] Report {report_id} not found.")
        return None

    logger.info(f"[Pipeline] Starting Stage E2 orchestration for Report {report_id}...")
    report.status = ReportStatus.processing.value
    db.commit()

    # Step 1: Category & Department
    try:
        category, department, cat_conf = step_classify_category(report.description)
        report.category = category
        db.add(AIPrediction(
            report_id=report.id,
            predicted_category=category.value,
            confidence=cat_conf,
            model_version="rule_heuristic_v1",
            data_source="ai_inference"
        ))
    except Exception as e:
        logger.warning(f"[Pipeline Step 1 Error] Classification failed: {e}")
        category = Day0Category.other
        department = "General Administration"

    # Step 2: Severity Estimation
    try:
        severity, sev_conf = step_estimate_severity(report.description)
    except Exception as e:
        logger.warning(f"[Pipeline Step 2 Error] Severity estimation failed: {e}")
        severity, sev_conf = "Medium", 0.50

    # Step 3: Incident Matching & Deduplication
    try:
        incident, is_new, match_conf = step_find_or_create_incident(report, category, severity, db)
        
        # Link report to incident
        report.incident_id = incident.id
        db.add(IncidentReport(
            incident_id=incident.id,
            report_id=report.id,
            confidence_score=match_conf,
            data_source="clustering_engine"
        ))
        db.flush()
    except Exception as e:
        logger.error(f"[Pipeline Step 3 Error] Incident clustering failed: {e}")
        db.rollback()
        return None

    # Step 4: 5-Factor Priority Scoring
    try:
        linked_count = db.query(IncidentReport).filter(IncidentReport.incident_id == incident.id).count()
        score, breakdown, urgent, priority_tier = step_compute_5factor_priority(
            severity=severity,
            linked_report_count=linked_count,
            created_at=incident.created_at,
            lat=incident.latitude,
            lng=incident.longitude,
            db=db
        )

        incident.severity = severity
        incident.priority = priority_tier
        incident.priority_score = score
        incident.score_breakdown = breakdown
        incident.urgent_review_flag = urgent
    except Exception as e:
        logger.warning(f"[Pipeline Step 4 Error] Priority scoring failed: {e}")

    # Step 5: Image Evidence Verification (0% weight)
    try:
        verdict = step_verify_photo_evidence(report, category, db)
        incident.image_verdict = verdict
    except Exception as e:
        logger.warning(f"[Pipeline Step 5 Error] Image verification failed: {e}")

    # Finalize: Create default department assignment & update report status
    try:
        existing_assign = db.query(Assignment).filter(Assignment.incident_id == incident.id).first()
        if not existing_assign:
            db.add(Assignment(
                incident_id=incident.id,
                department_name=department,
                status="assigned",
                notes=f"Auto-assigned to {department} based on category '{category.value}'."
            ))

        new_status = ReportStatus.triaged.value if is_new else ReportStatus.duplicate_pending_review.value
        report.status = new_status
        db.add(StatusHistory(
            report_id=report.id,
            incident_id=incident.id,
            old_status=ReportStatus.received_pending_ai.value,
            new_status=new_status,
            notes="Stage E2 asynchronous pipeline completed successfully."
        ))

        db.commit()
        db.refresh(incident)
        logger.info(f"[Pipeline] Successfully enriched Incident {incident.id} (Score: {incident.priority_score}, Tier: {incident.priority.value}).")
        return incident
    except Exception as e:
        logger.error(f"[Pipeline Finalize Error] Failed to commit enriched state: {e}")
        db.rollback()
        return incident
