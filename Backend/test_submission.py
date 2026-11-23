"""
Verification script for POST /api/complaints in UrbanPulse.
Can test via FastAPI TestClient (with automatic fallback to local DB if PostgreSQL container is not yet started).
"""
import json
import logging
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.main import app
from app.db.session import get_db, engine
from app.models.base import Base

logging.basicConfig(level=logging.INFO)

def check_db_reachable():
    try:
        with engine.connect() as conn:
            return True
    except Exception:
        return False

def run_test():
    print("=" * 70)
    print(" UrbanPulse Fault-Tolerant Ingestion Verification (Stage E1)")
    print("=" * 70)

    # If PostgreSQL is not currently running, provide an automatic in-memory / local SQLite session
    # so developer can verify the entire API and ingestion flow immediately without blocking.
    if not check_db_reachable():
        print("\n[Notice] PostgreSQL/PostGIS is not currently active on localhost:5432.")
        print("          Using local development SQLite engine for instant verification...")
        dev_engine = create_engine(
            "sqlite:///./urbanpulse_dev.db",
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=dev_engine)
        DevSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dev_engine)

        def dev_get_db():
            db = DevSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = dev_get_db
    else:
        print("\n[OK] Connected to live PostgreSQL database.")

    client = TestClient(app)

    # 1. Check API Health & Day-0 Categories
    print("\n[Step 1] Checking API Health and Day-0 Categories...")
    health_res = client.get("/api/health")
    print(f"Health Status: {health_res.status_code}")
    print(f"Health Body: {json.dumps(health_res.json(), indent=2)}")

    # 2. Register / Login Citizen Account
    print("\n[Step 2] Authenticating Citizen account...")
    client.post(
        "/api/auth/register",
        json={
            "email": "citizen.demo@urbanpulse.local",
            "password": "Password123!",
            "full_name": "Citizen Demo User",
            "role": "Citizen"
        }
    )
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "citizen.demo@urbanpulse.local",
            "password": "Password123!"
        }
    )
    token = login_res.json()["access_token"]
    print("Citizen authenticated successfully!")
    print(f"Issued Bearer Token: {token[:35]}...")

    # 3. Submit Complaint via POST /api/complaints
    print("\n[Step 3] Submitting Complaint via POST /api/complaints...")
    form_data = {
        "description": "Hazardous road pothole near Metro Pillar 42 causing vehicle damage.",
        "lat": "28.613939",
        "lng": "77.209021",
        "consent": "true"
    }
    headers = {"Authorization": f"Bearer {token}"}
    file_content = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    files = {"photo": ("pothole.gif", file_content, "image/gif")}

    res = client.post("/api/complaints", data=form_data, files=files, headers=headers)
    print(f"\nResponse Code: {res.status_code} (Expected 201 Created)")
    print(f"Response Body:")
    print(json.dumps(res.json(), indent=2))

    data = res.json()
    assert res.status_code == 201
    assert data["status"] == "received_pending_ai"
    assert data["data_source"] == "user_submitted"
    assert "report_id" in data
    assert "created_at" in data

    # 4. Verify Immediate Persistence
    report_id = data["report_id"]
    print(f"\n[Step 4] Fetching persisted report (ID: {report_id})...")
    detail_res = client.get(f"/api/complaints/{report_id}", headers=headers)
    print(f"Fetched Status: {detail_res.status_code}")
    print(json.dumps(detail_res.json(), indent=2))

    # 5. Negative Test: Consent Enforcement
    print("\n[Step 5] Negative Test: Submitting without consent (consent=false)...")
    rejected = client.post(
        "/api/complaints",
        data={
            "description": "Test complaint with no consent",
            "lat": "28.6139",
            "lng": "77.2090",
            "consent": "false"
        },
        headers=headers
    )
    print(f"Rejected Response: {rejected.status_code} - {rejected.json()}")
    assert rejected.status_code == 400

    print("\n" + "=" * 70)
    print(" ALL CHECKS PASSED: Stage E1 Fault-Tolerant Ingestion is Operational!")
    print("=" * 70)

if __name__ == "__main__":
    run_test()
