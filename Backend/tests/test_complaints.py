import io
from app.models.report import Report
from app.models.enums import Day0Category


def test_submit_complaint_success(client, citizen_token):
    """
    Test fault-tolerant complaint submission:
    - Returns 201 Created
    - Exact payload fields: report_id (prefixed rpt_), status="received_pending_ai",
      created_at ending in Z, data_source="user_submitted"
    - Database record persisted immediately
    """
    form_data = {
        "description": "Large pothole in the middle lane causing dangerous tire punctures.",
        "lat": "28.6139",
        "lng": "77.2090",
        "consent": "true"
    }
    headers = {"Authorization": f"Bearer {citizen_token}"}

    response = client.post("/api/complaints", data=form_data, headers=headers)
    assert response.status_code == 201, response.text
    
    data = response.json()
    assert "report_id" in data
    assert data["report_id"].startswith("rpt_")
    assert data["status"] == "received_pending_ai"
    assert data["data_source"] == "user_submitted"
    assert "created_at" in data
    assert data["created_at"].endswith("Z")

    # Verify retrieval
    get_res = client.get(f"/api/complaints/{data['report_id']}", headers=headers)
    assert get_res.status_code == 200
    report_data = get_res.json()
    assert report_data["id"] == data["report_id"]
    assert report_data["status"] in ("received_pending_ai", "triaged")
    assert report_data["data_source"] == "user_submitted"
    assert report_data["latitude"] == 28.6139
    assert report_data["longitude"] == 77.2090
    assert report_data["consent"] is True
    assert report_data["created_at"].endswith("Z")


def test_submit_complaint_with_photo(client, citizen_token):
    """
    Test complaint submission including photo attachment evidence.
    """
    form_data = {
        "description": "Broken streetlight pole with exposed wiring sparking on sidewalk.",
        "lat": "19.0760",
        "lng": "72.8777",
        "consent": "true"
    }
    headers = {"Authorization": f"Bearer {citizen_token}"}
    fake_photo = ("streetlight.jpg", io.BytesIO(b"fake_jpeg_image_data_bytes_12345"), "image/jpeg")

    response = client.post(
        "/api/complaints",
        data=form_data,
        files={"photo": fake_photo},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "received_pending_ai"
    assert data["data_source"] == "user_submitted"
    assert data["report_id"].startswith("rpt_")


def test_submit_complaint_consent_enforcement_rejected(client, citizen_token):
    """
    Strict rule: explicit consent=true is required.
    If consent is false or missing, reject with HTTP 400 Bad Request.
    """
    form_data = {
        "description": "Garbage dump overflowing outside apartment block.",
        "lat": "12.9716",
        "lng": "77.5946",
        "consent": "false"  # Explicitly withheld consent
    }
    headers = {"Authorization": f"Bearer {citizen_token}"}

    response = client.post("/api/complaints", data=form_data, headers=headers)
    assert response.status_code == 400
    assert "Consent is required" in response.json()["detail"]


def test_submit_complaint_unauthorized_missing_token(client):
    """
    Requires valid JWT token. Rejects with 401 or 403 if missing.
    """
    form_data = {
        "description": "Water pipe leak flooding the driveway.",
        "lat": "13.0827",
        "lng": "80.2707",
        "consent": "true"
    }
    response = client.post("/api/complaints", data=form_data)
    assert response.status_code in (401, 403)


def test_submit_complaint_invalid_coordinates(client, citizen_token):
    """
    Latitude must be between -90 and 90; longitude between -180 and 180.
    """
    form_data = {
        "description": "Blocked storm drain.",
        "lat": "95.0",  # Invalid latitude
        "lng": "77.2090",
        "consent": "true"
    }
    headers = {"Authorization": f"Bearer {citizen_token}"}

    response = client.post("/api/complaints", data=form_data, headers=headers)
    assert response.status_code == 400
    assert "Invalid latitude" in response.json()["detail"]


def test_list_complaints_rbac(client, citizen_token, admin_token):
    """
    Verify RBAC for listing complaints:
    Citizen sees their own reports; Admin sees all reports.
    """
    # 1. Citizen submits a report
    client.post(
        "/api/complaints",
        data={
            "description": "Citizen test issue for listing.",
            "lat": "28.5000",
            "lng": "77.1000",
            "consent": "true"
        },
        headers={"Authorization": f"Bearer {citizen_token}"}
    )

    # 2. Citizen lists complaints
    res_citizen = client.get("/api/complaints", headers={"Authorization": f"Bearer {citizen_token}"})
    assert res_citizen.status_code == 200
    data_citizen = res_citizen.json()
    assert data_citizen["total"] >= 1
    for item in data_citizen["items"]:
        assert item["created_at"].endswith("Z")

    # 3. Admin lists complaints
    res_admin = client.get("/api/complaints", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin["total"] >= data_citizen["total"]


def test_locked_day0_config_endpoint(client):
    """
    Verify Day-0 locked categories, department mappings, and priority weights.
    """
    response = client.get("/api/config/day0")
    assert response.status_code == 200
    data = response.json()
    
    # 6 locked categories
    assert data["locked_categories"] == [
        "road_damage",
        "garbage_sanitation",
        "streetlight_electrical",
        "water_supply",
        "drainage_flooding",
        "other"
    ]
    # Priority weights (0.40S + 0.20R + 0.15T + 0.15L + 0.10E)
    weights = data["priority_weights"]
    assert weights["S"] == 0.40
    assert weights["R"] == 0.20
    assert weights["T"] == 0.15
    assert weights["L"] == 0.15
    assert weights["E"] == 0.10

    # Department mappings
    assert data["department_mappings"]["road_damage"] == "Public Works"
    assert data["department_mappings"]["garbage_sanitation"] == "Solid Waste Management"
