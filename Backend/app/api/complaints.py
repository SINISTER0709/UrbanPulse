import os
import uuid
import logging
from typing import Annotated, Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from geoalchemy2.elements import WKTElement

from app.config import settings
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.report import Report, generate_report_id
from app.models.evidence import ImageEvidence
from app.models.enums import ReportStatus, DataSource, UserRole, Day0Category
from app.schemas.report import ComplaintCreateResponse, ReportDetailResponse, ComplaintListResponse, format_utc_z

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/complaints", tags=["Complaints Ingestion"])


def run_background_pipeline(report_id: str, db: Session):
    """
    Asynchronous Stage E2 background worker.
    Runs Track A, B, F, and C pipeline with isolated error handling.
    Fault-tolerant guarantee: If anything fails here, the 201 Created ingestion is already complete.
    """
    from app.services.pipeline import orchestrate_report_pipeline
    try:
        orchestrate_report_pipeline(report_id, db)
    except Exception as exc:
        logger.error(f"[Pipeline Worker Error] Background processing failed for report {report_id}: {exc}")


@router.post("", response_model=ComplaintCreateResponse, status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    description: Annotated[str, Form(..., description="Citizen detailed description of the municipal issue")],
    consent: Annotated[str, Form(..., description="Explicit citizen consent flag; must be true")],
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    lat: Annotated[float | None, Form(description="Latitude coordinate between -90 and 90")] = None,
    lng: Annotated[float | None, Form(description="Longitude coordinate between -180 and 180")] = None,
    latitude: Annotated[float | None, Form(description="Alias for lat")] = None,
    longitude: Annotated[float | None, Form(description="Alias for lng")] = None,
    address: Annotated[str | None, Form(description="Optional reverse-geocoded street address")] = None,
    photo: Annotated[UploadFile | None, File(description="Optional photographic evidence")] = None,
    photos: Annotated[List[UploadFile] | None, File(description="Optional multiple photographic evidence")] = None,
):
    """
    Fault-Tolerant Citizen Complaint Ingestion Endpoint.

    Strict Requirements:
    1. Authorization: Bearer <jwt> with valid user account.
    2. Explicit consent=true enforcement: minimal personal data policy.
    3. Spatial indexing: Persisted as PostGIS Geometry(POINT, 4326) with GIST indexing.
    4. Immediate persistence: Status is set to 'received_pending_ai' and data_source to 'user_submitted'.
    5. Returns 201 Created immediately with report_id (rpt_...), status, created_at (UTC Z), data_source.
    """
    # Resolve coordinate parameters
    final_lat = lat if lat is not None else latitude
    final_lng = lng if lng is not None else longitude
    if final_lat is None or final_lng is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coordinates required: provide either (lat, lng) or (latitude, longitude)."
        )

    # 1. Enforce explicit citizen consent
    consent_normalized = str(consent).strip().lower()
    if consent_normalized not in ("true", "1", "yes"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required to submit a complaint. Please provide consent=true."
        )

    # 2. Validate input coordinates
    if not (-90.0 <= final_lat <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid latitude {final_lat}. Must be between -90.0 and 90.0 degrees."
        )
    if not (-180.0 <= final_lng <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid longitude {final_lng}. Must be between -180.0 and 180.0 degrees."
        )

    # 3. Validate description
    clean_description = description.strip()
    if not clean_description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint description cannot be empty."
        )

    # 4. Initialize report record with Day-0 locked defaults and 'rpt_' ID
    report_id = generate_report_id()
    # PostGIS WKT format: POINT(longitude latitude)
    point_geom = WKTElement(f"POINT({final_lng} {final_lat})", srid=4326)
    utc_now = datetime.now(timezone.utc)

    new_report = Report(
        id=report_id,
        user_id=current_user.id,
        description=clean_description,
        category=None,  # Pending AI triage
        status=ReportStatus.received_pending_ai.value,
        data_source=DataSource.user_submitted.value,
        consent=True,
        address=address,
        location=point_geom,
        latitude=final_lat,
        longitude=final_lng,
        created_at=utc_now,
        updated_at=utc_now,
    )

    db.add(new_report)

    # 5. Persist optional photo evidence (support single and multiple photos)
    all_uploads: List[UploadFile] = []
    if photo and photo.filename:
        all_uploads.append(photo)
    if photos:
        for p in photos:
            if p and p.filename and p not in all_uploads:
                all_uploads.append(p)

    for up_photo in all_uploads[:5]:
        try:
            file_ext = os.path.splitext(up_photo.filename)[1]
            safe_filename = f"{report_id}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_destination = os.path.join(settings.UPLOAD_DIR, safe_filename)

            contents = await up_photo.read()
            with open(file_destination, "wb") as f:
                f.write(contents)

            evidence = ImageEvidence(
                report_id=report_id,
                file_path=file_destination,
                file_name=up_photo.filename,
                mime_type=up_photo.content_type,
                file_size_bytes=len(contents),
                verification_status="pending",
                data_source="user_upload"
            )
            db.add(evidence)
        except Exception as upload_err:
            logger.warning(f"Failed to save photographic evidence for report {report_id}: {upload_err}")
            # Non-blocking: continue persisting the report itself

    # 6. Commit to database immediately
    db.commit()
    db.refresh(new_report)

    # 7. Asynchronous pipeline trigger (Stage E2)
    background_tasks.add_task(run_background_pipeline, report_id, db)

    # 8. Return 201 Created response
    return ComplaintCreateResponse(
        report_id=new_report.id,
        status=new_report.status,
        created_at=format_utc_z(new_report.created_at),
        data_source=new_report.data_source,
    )


def serialize_report_detail(item: Report) -> ReportDetailResponse:
    eff_status = item.status
    eff_cat = item.category
    inc_st = None
    inc_id = None
    if item.incident:
        inc_id = item.incident.id
        inc_st = item.incident.status.value if hasattr(item.incident.status, "value") else str(item.incident.status)
        if inc_st in ["assigned", "in_progress", "resolved", "closed"]:
            eff_status = inc_st
        if item.incident.category:
            eff_cat = item.incident.category

    photo_urls = [
        f"/uploads/{os.path.basename(ev.file_path)}"
        for ev in item.image_evidence
        if ev.file_path
    ]

    return ReportDetailResponse(
        id=item.id,
        description=item.description,
        category=eff_cat,
        status=eff_status,
        data_source=item.data_source,
        latitude=item.latitude,
        longitude=item.longitude,
        address=item.address,
        consent=item.consent,
        incident_id=inc_id,
        incident_status=inc_st,
        photos=photo_urls,
        created_at=format_utc_z(item.created_at),
        updated_at=format_utc_z(item.updated_at),
    )


@router.get("", response_model=ComplaintListResponse)
def list_complaints(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[Day0Category] = Query(None),
    data_source: Optional[str] = Query(None),
):
    """
    List complaints with RBAC scoping:
    - Citizens: view only their own submitted complaints.
    - Admins & Department: view complaints across the city with multi-parameter filtering.
    """
    query = db.query(Report)

    user_role_str = str(current_user.role.value if hasattr(current_user.role, "value") else current_user.role)
    if user_role_str == UserRole.Citizen.value:
        query = query.filter(Report.user_id == current_user.id)

    if status_filter:
        query = query.filter(Report.status == status_filter)
    if category:
        query = query.filter(Report.category == category)
    if data_source:
        query = query.filter(Report.data_source == data_source)

    total = query.count()
    items = query.order_by(desc(Report.created_at)).offset(skip).limit(limit).all()

    return ComplaintListResponse(
        total=total,
        items=[serialize_report_detail(item) for item in items]
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_complaint(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Fetches the details of an existing complaint report with RBAC verification.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found."
        )

    user_role_str = str(current_user.role.value if hasattr(current_user.role, "value") else current_user.role)
    if user_role_str == UserRole.Citizen.value and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view your own complaints."
        )

    return serialize_report_detail(report)
