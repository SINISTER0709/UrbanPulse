import pytest
from app.models.enums import Day0Category, IncidentStatus, IncidentPriority, UserRole
from app.models.poi import POI
from app.services.pipeline import orchestrate_report_pipeline


def test_mvp_pipeline_execution(client, citizen_token, db_session):
    """
    Test Stage E2 MVP Case from PDF specification:
    Input: "Large pothole outside ABC School causing traffic problems.", lat=28.4506, lng=77.5842
    Expected:
    - Persisted report_id="rpt_..."
    - Enriched Incident record with:
      - category="road_damage"
      - severity="High"
      - Location risk (L) boosted (school proximity)
      - priority_score=55.0 (S=30.0, R=10.0, T=0.0, L=15.0, E=0.0)
      - Auto-assigned to "Public Works"
    """
    # 1. Pre-seed ABC Public School POI
    db_session.add(POI(
        id="poi_abc_school",
        name="ABC Public School",
        poi_type="school",
        latitude=28.4506,
        longitude=77.5842,
        buffer_meters=250.0,
        data_source="municipal_gis"
    ))
    db_session.commit()

    # 2. Ingest complaint
    form_data = {
        "description": "Large pothole outside ABC School causing traffic problems.",
        "lat": "28.4506",
        "lng": "77.5842",
        "consent": "true"
    }
    headers = {"Authorization": f"Bearer {citizen_token}"}
    create_res = client.post("/api/complaints", data=form_data, headers=headers)
    assert create_res.status_code == 201
    report_id = create_res.json()["report_id"]

    # 3. Retrieve incident enriched by Stage E2 background pipeline
    from app.models.report import Report
    from app.models.incident import Incident
    report = db_session.query(Report).filter(Report.id == report_id).first()
    assert report is not None
    assert report.incident_id is not None
    incident = db_session.query(Incident).filter(Incident.id == report.incident_id).first()
    assert incident is not None
    assert incident.id.startswith("inc_")
    assert incident.category == Day0Category.road_damage
    assert incident.severity == "High"
    assert incident.priority_score == 55.0

    breakdown = incident.score_breakdown
    assert breakdown["S"] == 30.0
    assert breakdown["R"] == 10.0
    assert breakdown["T"] == 0.0
    assert breakdown["L"] == 15.0
    assert breakdown["E"] == 0.0

    # 4. Verify department auto-assignment
    assert len(incident.assignments) >= 1
    assert incident.assignments[0].department_name == "Public Works"


def test_admin_override_workflow(client, admin_token, citizen_token, db_session):
    """
    Test Human-in-the-Loop Admin Override from Page 3 of PDF:
    PATCH /api/incidents/inc_42/override {"severity": "Critical", "reason": "School bus route blocked"}
    Expected:
    - Updated severity="Critical"
    - Recalculated priority score (S becomes 40.0, total becomes 65.0)
    - urgent_review_flag=True
    - admin_reviews audit row logged
    """
    # 1. Ingest complaint (background pipeline processes it automatically)
    form_data = {
        "description": "Pothole in roadway causing minor delays.",
        "lat": "28.4506",
        "lng": "77.5842",
        "consent": "true"
    }
    headers = {"Authorization": f"Bearer {citizen_token}"}
    create_res = client.post("/api/complaints", data=form_data, headers=headers)
    assert create_res.status_code == 201
    report_id = create_res.json()["report_id"]

    # Retrieve incident created by background pipeline
    from app.models.report import Report
    from app.models.incident import Incident
    report = db_session.query(Report).filter(Report.id == report_id).first()
    assert report is not None
    assert report.incident_id is not None
    incident = db_session.query(Incident).filter(Incident.id == report.incident_id).first()
    assert incident is not None

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Execute Admin Override
    override_payload = {
        "severity": "Critical",
        "reason": "School bus route blocked"
    }
    override_res = client.patch(
        f"/api/incidents/{incident.id}/override",
        json=override_payload,
        headers=admin_headers
    )
    assert override_res.status_code == 200, override_res.text
    data = override_res.json()
    assert data["severity"] == "Critical"
    assert data["urgent_review_flag"] is True
    assert data["priority"] == "critical"
    assert data["score_breakdown"]["S"] == 40.0
    assert data["priority_score"] >= 50.0

    # 3. Verify audit record in admin_reviews
    detail_res = client.get(f"/api/incidents/{incident.id}", headers=admin_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["admin_reviews"]) >= 1
    review = detail_data["admin_reviews"][0]
    assert review["decision"] == "override"
    assert "School bus route blocked" in review["notes"]


def test_admin_override_rbac_forbidden_for_citizen(client, citizen_token, db_session):
    """
    Security check: Citizens must be strictly forbidden from overriding incidents (403 Forbidden).
    """
    form_data = {
        "description": "Streetlight failure.",
        "lat": "28.5000",
        "lng": "77.2000",
        "consent": "true"
    }
    headers = {"Authorization": f"Bearer {citizen_token}"}
    create_res = client.post("/api/complaints", data=form_data, headers=headers)
    report_id = create_res.json()["report_id"]
    from app.models.report import Report
    from app.models.incident import Incident
    report = db_session.query(Report).filter(Report.id == report_id).first()
    incident = db_session.query(Incident).filter(Incident.id == report.incident_id).first()

    # Citizen attempts override
    rejected_res = client.patch(
        f"/api/incidents/{incident.id}/override",
        json={"severity": "Critical", "reason": "Unauthorized attempt"},
        headers=headers
    )
    assert rejected_res.status_code == 403
    assert "Operation not permitted" in rejected_res.json()["detail"]


def test_status_transition_and_assignment(client, admin_token, citizen_token, db_session):
    """
    Test status transitions and manual department assignments with audit logging.
    """
    form_data = {
        "description": "Flooded drainage channel near residential block.",
        "lat": "28.6000",
        "lng": "77.3000",
        "consent": "true"
    }
    create_res = client.post("/api/complaints", data=form_data, headers={"Authorization": f"Bearer {citizen_token}"})
    report_id = create_res.json()["report_id"]
    from app.models.report import Report
    from app.models.incident import Incident
    report = db_session.query(Report).filter(Report.id == report_id).first()
    incident = db_session.query(Incident).filter(Incident.id == report.incident_id).first()

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Update status to in_progress
    status_res = client.patch(
        f"/api/incidents/{incident.id}/status",
        json={"status": "in_progress", "notes": "Crews dispatched to site"},
        headers=admin_headers
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "in_progress"

    # 2. Add department assignment
    assign_res = client.post(
        f"/api/incidents/{incident.id}/assign",
        json={"department_name": "Stormwater Drainage", "notes": "Assigned pump crew"},
        headers=admin_headers
    )
    assert assign_res.status_code == 200

    # 3. Check incident detail
    detail_res = client.get(f"/api/incidents/{incident.id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assignments = detail_res.json()["assignments"]
    assert any(a["department_name"] == "Stormwater Drainage" for a in assignments)
