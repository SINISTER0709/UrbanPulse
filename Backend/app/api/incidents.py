import os
import logging
from typing import Annotated, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc

from app.api.deps import get_db, get_current_user, require_admin, require_role
from app.models.user import User
from app.models.incident import Incident, IncidentReport, generate_incident_id
from app.models.report import Report
from app.models.evidence import ImageEvidence
from app.models.review import AdminReview
from app.models.audit import PriorityHistory, StatusHistory
from app.models.assignment import Assignment
from app.models.enums import UserRole, IncidentStatus, IncidentPriority, Day0Category, ReportStatus
from app.schemas.incident import (
    IncidentResponse,
    IncidentDetailResponse,
    LocationCoords,
    AdminOverrideRequest,
    DuplicateDecisionRequest,
    StatusTransitionRequest,
    AssignmentRequest,
    AssignmentResponse,
    AdminReviewResponse,
)
from app.schemas.report import format_utc_z, ReportDetailResponse
from app.core.shared_config import PRIORITY_WEIGHTS, CATEGORY_DEPARTMENT_MAPPINGS

logger = logging.getLogger("urbanpulse.api.incidents")

router = APIRouter(prefix="/incidents", tags=["Incidents & Admin Override"])


def serialize_incident_response(inc: Incident, db: Session) -> IncidentResponse:
    report_count = db.query(IncidentReport).filter(IncidentReport.incident_id == inc.id).count()
    loc = LocationCoords(latitude=inc.latitude, longitude=inc.longitude) if inc.latitude is not None and inc.longitude is not None else None

    asgns = [
        AssignmentResponse(
            id=a.id,
            department_name=a.department_name,
            assigned_user_id=a.assigned_user_id,
            status=a.status,
            notes=a.notes,
            assigned_at=format_utc_z(a.assigned_at),
        )
        for a in inc.assignments
    ] if inc.assignments else []

    revs = [
        AdminReviewResponse(
            id=rev.id,
            decision=rev.decision,
            notes=rev.notes,
            reviewer_user_id=rev.reviewer_user_id,
            reviewed_at=format_utc_z(rev.reviewed_at),
        )
        for rev in inc.admin_reviews
    ] if inc.admin_reviews else []

    report_links = db.query(IncidentReport).filter(IncidentReport.incident_id == inc.id).all()
    rep_ids = [rl.report_id for rl in report_links]
    reports_data = db.query(Report).filter(Report.id.in_(rep_ids)).all() if rep_ids else []
    r_list = [
        ReportDetailResponse(
            id=r.id,
            description=r.description,
            category=r.category,
            status=r.status,
            data_source=r.data_source,
            latitude=r.latitude,
            longitude=r.longitude,
            address=r.address,
            consent=r.consent,
            created_at=format_utc_z(r.created_at),
            updated_at=format_utc_z(r.updated_at),
        )
        for r in reports_data
    ]

    evidence_records = db.query(ImageEvidence).filter(ImageEvidence.report_id.in_(rep_ids)).all() if rep_ids else []
    photo_urls = [f"/uploads/{os.path.basename(ev.file_path)}" for ev in evidence_records if ev.file_path]

    resolved_address = inc.address
    if not resolved_address and reports_data and reports_data[0].address:
        resolved_address = reports_data[0].address

    return IncidentResponse(
        id=inc.id,
        title=inc.title,
        summary_text=inc.summary_text,
        category=inc.category,
        status=inc.status,
        priority=inc.priority,
        severity=inc.severity,
        priority_score=inc.priority_score,
        score_breakdown=inc.score_breakdown or {},
        urgent_review_flag=inc.urgent_review_flag,
        image_verdict=inc.image_verdict,
        data_source=inc.data_source,
        latitude=inc.latitude,
        longitude=inc.longitude,
        location=loc,
        address=resolved_address,
        photos=photo_urls,
        created_at=format_utc_z(inc.created_at),
        updated_at=format_utc_z(inc.updated_at),
        linked_reports_count=max(1, report_count),
        reports=r_list,
        assignments=asgns,
        admin_reviews=revs,
    )


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status: Optional[IncidentStatus] = Query(None),
    category: Optional[Day0Category] = Query(None),
    priority: Optional[IncidentPriority] = Query(None),
    urgent_only: Optional[bool] = Query(False),
    min_score: Optional[float] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List incidents with multi-factor filtering, priority sorting, and urgent-review flags.
    """
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if category:
        query = query.filter(Incident.category == category)
    if priority:
        query = query.filter(Incident.priority == priority)
    if urgent_only:
        query = query.filter(Incident.urgent_review_flag == True)
    if min_score is not None:
        query = query.filter(Incident.priority_score >= min_score)

    incidents = query.order_by(desc(Incident.priority_score), desc(Incident.created_at)).offset(skip).limit(limit).all()
    return [serialize_incident_response(inc, db) for inc in incidents]


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(
    incident_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Retrieves full details of an incident including linked citizen reports,
    assignments, and admin review audit history.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )

    linked_reports_data = (
        db.query(Report)
        .join(IncidentReport, Report.id == IncidentReport.report_id)
        .filter(IncidentReport.incident_id == inc.id)
        .all()
    )

    base = serialize_incident_response(inc, db)
    base_data = base.model_dump()
    base_data["linked_reports"] = [
        ReportDetailResponse(
            id=r.id,
            description=r.description,
            category=r.category,
            status=r.status,
            data_source=r.data_source,
            latitude=r.latitude,
            longitude=r.longitude,
            consent=r.consent,
            created_at=format_utc_z(r.created_at),
            updated_at=format_utc_z(r.updated_at),
        )
        for r in linked_reports_data
    ]
    return IncidentDetailResponse(**base_data)


@router.patch("/{incident_id}/override", response_model=IncidentResponse)
def admin_override_incident(
    incident_id: str,
    override_data: AdminOverrideRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Human-in-the-Loop Admin Override Endpoint (Stage E2 Core Deliverable).
    Example: PATCH /api/incidents/inc_42/override {"severity": "Critical", "reason": "School bus route blocked"}

    Actions:
    1. RBAC: Enforces Admin role.
    2. Logs every override into admin_reviews audit row with reason and reviewer ID.
    3. Updates category/severity and recalculates the 5-factor priority score.
    4. Records priority changes in priority_history.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )

    old_priority_val = inc.priority.value if hasattr(inc.priority, "value") else str(inc.priority)
    old_severity = inc.severity

    # Find primary linked report if available to satisfy legacy constraints
    primary_report_id = None
    if inc.reports:
        primary_report_id = inc.reports[0].id
    else:
        first_link = db.query(IncidentReport).filter(IncidentReport.incident_id == inc.id).first()
        if first_link:
            primary_report_id = first_link.report_id

    # 1. Log to admin_reviews table
    review_record = AdminReview(
        incident_id=inc.id,
        report_id=primary_report_id,
        reviewer_user_id=current_user.id,
        decision="override",
        notes=override_data.reason,
        data_source="admin_override_api"
    )
    db.add(review_record)

    # 2. Apply Category override
    if override_data.category:
        inc.category = override_data.category
        new_dept = CATEGORY_DEPARTMENT_MAPPINGS.get(inc.category.value, "General Administration")
        # Update or add assignment for new department
        assignment = db.query(Assignment).filter(Assignment.incident_id == inc.id).first()
        if assignment:
            assignment.department_name = new_dept
            assignment.notes = f"Department updated to {new_dept} via admin category override."

        # Sync category to all linked citizen reports
        report_links = db.query(IncidentReport).filter(IncidentReport.incident_id == inc.id).all()
        linked_rep_ids = [rl.report_id for rl in report_links]
        if linked_rep_ids:
            db.query(Report).filter(Report.id.in_(linked_rep_ids)).update(
                {Report.category: override_data.category},
                synchronize_session=False
            )

    # 3. Apply Severity override & recalculate 5-factor priority score
    if override_data.severity:
        inc.severity = override_data.severity
        severity_map = {"Critical": 100.0, "High": 75.0, "Medium": 50.0, "Low": 25.0}
        raw_s = severity_map.get(override_data.severity, 75.0)
        new_s_score = round(PRIORITY_WEIGHTS["S"] * raw_s, 1)

        new_breakdown = dict(inc.score_breakdown or {"S": 30.0, "R": 10.0, "T": 0.0, "L": 15.0, "E": 0.0})
        new_breakdown["S"] = new_s_score
        
        # Calculate new total priority score
        inc.score_breakdown = new_breakdown
        inc.priority_score = round(sum(new_breakdown.values()), 1)
        flag_modified(inc, "score_breakdown")

        if override_data.severity == "Critical":
            inc.urgent_review_flag = True
            inc.priority = IncidentPriority.critical
        elif inc.priority_score >= 75.0:
            inc.priority = IncidentPriority.critical
        elif inc.priority_score >= 50.0:
            inc.priority = IncidentPriority.high
        else:
            inc.priority = IncidentPriority.medium

    # 4. Manual Priority override if explicitly supplied
    if override_data.priority:
        inc.priority = override_data.priority

    new_priority_val = inc.priority.value if hasattr(inc.priority, "value") else str(inc.priority)

    # 5. Log to priority_history if priority or severity changed
    if old_priority_val != new_priority_val or old_severity != inc.severity:
        db.add(PriorityHistory(
            incident_id=inc.id,
            old_priority=old_priority_val,
            new_priority=new_priority_val,
            changed_by_user_id=current_user.id,
            reason=f"Admin override: {override_data.reason} (Severity: {old_severity} -> {inc.severity})"
        ))

    inc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(inc)

    logger.info(f"[Admin Override] Incident {inc.id} overridden by Admin {current_user.id}: {override_data.reason}")
    return serialize_incident_response(inc, db)


@router.post("/{incident_id}/duplicate", response_model=IncidentResponse)
def handle_duplicate_decision(
    incident_id: str,
    decision_in: DuplicateDecisionRequest,
    current_user: Annotated[User, Depends(require_role([UserRole.Admin, UserRole.Department]))],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Duplicate confirm / reject endpoint.
    - If is_duplicate=True: Confirms report is a duplicate and links it to this incident.
    - If is_duplicate=False: Splits report away from this incident and spawns a standalone incident.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    report = db.query(Report).filter(Report.id == decision_in.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if decision_in.is_duplicate:
        # Confirm duplicate: Ensure link exists
        link = db.query(IncidentReport).filter(
            IncidentReport.incident_id == inc.id,
            IncidentReport.report_id == report.id
        ).first()
        if not link:
            db.add(IncidentReport(
                incident_id=inc.id,
                report_id=report.id,
                confidence_score=1.0,
                data_source="manual_confirmation"
            ))
        report.incident_id = inc.id
        report.status = "duplicate_confirmed"
    else:
        # Reject duplicate: Remove link and create separate standalone incident
        db.query(IncidentReport).filter(
            IncidentReport.incident_id == inc.id,
            IncidentReport.report_id == report.id
        ).delete()

        new_inc = Incident(
            id=generate_incident_id(),
            title=f"Split Issue: {report.description[:50]}",
            summary_text=report.description,
            category=report.category or inc.category,
            status=IncidentStatus.open,
            severity=inc.severity,
            priority=inc.priority,
            address=report.address,
            latitude=report.latitude,
            longitude=report.longitude,
            data_source="duplicate_split"
        )
        db.add(new_inc)
        db.flush()
        report.incident_id = new_inc.id
        report.status = ReportStatus.triaged.value
        db.add(IncidentReport(
            incident_id=new_inc.id,
            report_id=report.id,
            confidence_score=1.0,
            data_source="duplicate_split"
        ))

    db.add(AdminReview(
        incident_id=inc.id,
        report_id=report.id,
        reviewer_user_id=current_user.id,
        decision="duplicate_confirm" if decision_in.is_duplicate else "duplicate_reject",
        notes=decision_in.reason or "Duplicate triage decision"
    ))

    db.commit()
    db.refresh(inc)
    return serialize_incident_response(inc, db)


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: str,
    status_in: StatusTransitionRequest,
    current_user: Annotated[User, Depends(require_role([UserRole.Admin, UserRole.Department]))],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Transitions incident status and records audit history.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    old_status = inc.status.value if hasattr(inc.status, "value") else str(inc.status)
    new_status = status_in.status.value if hasattr(status_in.status, "value") else str(status_in.status)

    inc.status = status_in.status
    if status_in.status in [IncidentStatus.resolved, IncidentStatus.closed]:
        inc.urgent_review_flag = False
    inc.updated_at = datetime.utcnow()

    # Sync status to all linked citizen reports
    report_links = db.query(IncidentReport).filter(IncidentReport.incident_id == inc.id).all()
    linked_rep_ids = [rl.report_id for rl in report_links]
    if linked_rep_ids:
        db.query(Report).filter(Report.id.in_(linked_rep_ids)).update(
            {Report.status: new_status},
            synchronize_session=False
        )
        for rep_id in linked_rep_ids:
            db.add(StatusHistory(
                report_id=rep_id,
                incident_id=inc.id,
                old_status=old_status,
                new_status=new_status,
                notes=f"Updated via incident status transition: {status_in.notes or ''}"
            ))

    db.add(StatusHistory(
        incident_id=inc.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_user_id=current_user.id,
        notes=status_in.notes
    ))

    db.commit()
    db.refresh(inc)
    return serialize_incident_response(inc, db)


@router.post("/{incident_id}/assign", response_model=IncidentResponse)
def assign_incident_department(
    incident_id: str,
    assign_in: AssignmentRequest,
    current_user: Annotated[User, Depends(require_role([UserRole.Admin, UserRole.Department]))],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Assigns incident to municipal department or personnel.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    # If incident is open or triaged, promote status to assigned
    if inc.status in [IncidentStatus.open, IncidentStatus.triaged]:
        inc.status = IncidentStatus.assigned
        inc.updated_at = datetime.utcnow()

    assignment = Assignment(
        incident_id=inc.id,
        department_name=assign_in.department_name,
        assigned_user_id=assign_in.assigned_user_id,
        assigned_by_user_id=current_user.id,
        notes=assign_in.notes,
        due_date=assign_in.due_date,
        status="assigned"
    )
    db.add(assignment)

    # Sync linked citizen reports to assigned status
    report_links = db.query(IncidentReport).filter(IncidentReport.incident_id == inc.id).all()
    linked_rep_ids = [rl.report_id for rl in report_links]
    if linked_rep_ids:
        db.query(Report).filter(Report.id.in_(linked_rep_ids)).update(
            {Report.status: ReportStatus.assigned.value},
            synchronize_session=False
        )
    db.commit()
    db.refresh(inc)
    return serialize_incident_response(inc, db)


@router.post("/{incident_id}/action-brief")
def generate_incident_action_brief(
    incident_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Track F Deliverable:
    RAG-grounded advisory action brief with cited SOP source excerpts and mandatory disclaimer.
    Called directly by Track D Frontend SOP brief viewer.
    """
    from app.services.rag_service import generate_action_brief

    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    cat_val = inc.category.value if hasattr(inc.category, "value") else str(inc.category)
    sev_val = inc.severity or "Medium"

    return generate_action_brief(
        incident_id=inc.id,
        category=cat_val,
        severity=sev_val,
        location_context="school_access" if inc.urgent_review_flag else "low_exposure",
        summary_text=inc.summary_text,
    )

