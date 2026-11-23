import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_track_a_category_analysis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/analyze/category",
            json={"text": "Large pothole outside ABC School causing traffic problems."},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["category"] in [
            "road_damage",
            "garbage_sanitation",
            "streetlight_electrical",
            "water_supply",
            "drainage_flooding",
            "other",
        ]
        assert "department" in data
        assert "fallback_used" in data


@pytest.mark.asyncio
async def test_track_b_severity_analysis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/analyze/severity",
            json={
                "text": "Large pothole outside ABC School causing traffic problems.",
                "submitted_at": "2026-11-21T08:30:00Z",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["severity"] in ["Low", "Medium", "High", "Critical"]
        assert 0.0 <= data["model_confidence"] <= 1.0


@pytest.mark.asyncio
async def test_track_c_evidence_analysis_no_image():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/evidence/analyze",
            data={"reported_category": "road_damage"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["verdict"] == "Not Provided"
        assert data["scoring_weight"] == 0.0


@pytest.mark.asyncio
async def test_track_f_priority_calculate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/priority/calculate",
            json={"S": 75.0, "R": 50.0, "T": 0.0, "L": 100.0, "E": 0.0},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["priority_score"] == 55.0
        assert data["breakdown"] == {"S": 30.0, "R": 10.0, "T": 0.0, "L": 15.0, "E": 0.0}
        assert data["urgent_review_flag"] is False


@pytest.mark.asyncio
async def test_track_f_analytics_hotspots():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/analytics/hotspots?category=road_damage&days=30")
        assert res.status_code == 200
        data = res.json()
        assert "clusters" in data
        assert "trends" in data


@pytest.mark.asyncio
async def test_track_f_incidents_match():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/incidents/match",
            json={
                "text": "Large pothole outside ABC School causing traffic problems.",
                "category": "road_damage",
                "lat": 28.4506,
                "lng": 77.5842,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "candidates" in data
        assert data["category"] == "road_damage"


@pytest.mark.asyncio
async def test_track_f_action_brief_generation():
    from app.services.rag_service import generate_action_brief
    brief = generate_action_brief(
        incident_id="inc_test_1",
        category="road_damage",
        severity="Critical",
        location_context="school_access",
        summary_text="Deep pothole near school entrance"
    )
    assert "brief" in brief
    assert "sources" in brief
    assert brief["disclaimer"] == "Advisory only, not municipal policy."

