import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.evidence_router import WEIGHTS_PATH
from app.main import app

client = TestClient(app)


def make_test_image_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (128, 128), color=(120, 120, 120)).save(buf, format="JPEG")
    return buf.getvalue()


def make_mock_model(detections: list[tuple[int, float]]):
    """Builds a lightweight fake YOLO model returning [(cls_id, conf), ...]."""
    names = {0: "pothole", 1: "litter", 2: "streetlight", 3: "water_leak", 4: "flooding"}
    boxes = [SimpleNamespace(cls=[cls_id], conf=[conf]) for cls_id, conf in detections]
    fake_result = SimpleNamespace(names=names, boxes=boxes)
    return SimpleNamespace(predict=lambda *args, **kwargs: [fake_result])


def test_not_provided_when_no_image():
    resp = client.post("/api/evidence/analyze", data={"reported_category": "road_damage"})
    assert resp.status_code == 200
    assert resp.json() == {"verdict": "Not Provided", "detections": [], "scoring_weight": 0.0}


def test_visual_match_pothole():
    with patch("app.evidence_router.get_model", return_value=make_mock_model([(0, 0.91)])):
        resp = client.post(
            "/api/evidence/analyze",
            data={"reported_category": "road_damage"},
            files={"image": ("pothole.jpg", make_test_image_bytes(), "image/jpeg")},
        )
    assert resp.status_code == 200
    assert resp.json() == {
        "verdict": "Visual Match",
        "detections": [{"label": "pothole", "confidence": 0.91}],
        "scoring_weight": 0.0,
    }


def test_mismatch_when_confident_different_problem():
    with patch("app.evidence_router.get_model", return_value=make_mock_model([(0, 0.87)])):
        resp = client.post(
            "/api/evidence/analyze",
            data={"reported_category": "garbage_sanitation"},
            files={"image": ("pothole.jpg", make_test_image_bytes(), "image/jpeg")},
        )
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "Mismatch"
    assert resp.json()["scoring_weight"] == 0.0


def test_inconclusive_when_weak_cross_class_detection():
    # pothole detected at 0.48 (< 0.55 mismatch threshold) against water_supply -> Inconclusive
    with patch("app.evidence_router.get_model", return_value=make_mock_model([(0, 0.48)])):
        resp = client.post(
            "/api/evidence/analyze",
            data={"reported_category": "water_supply"},
            files={"image": ("ambiguous.jpg", make_test_image_bytes(), "image/jpeg")},
        )
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "Inconclusive"
    assert resp.json()["scoring_weight"] == 0.0


def test_litter_lower_match_threshold():
    # litter at 0.28 passes MATCH_THRESH["litter"] = 0.25
    with patch("app.evidence_router.get_model", return_value=make_mock_model([(1, 0.28)])):
        resp = client.post(
            "/api/evidence/analyze",
            data={"reported_category": "garbage_sanitation"},
            files={"image": ("trash.jpg", make_test_image_bytes(), "image/jpeg")},
        )
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "Visual Match"
    assert resp.json()["detections"] == [{"label": "litter", "confidence": 0.28}]


def test_other_category_always_inconclusive():
    with patch("app.evidence_router.get_model", return_value=make_mock_model([(0, 0.88)])):
        resp = client.post(
            "/api/evidence/analyze",
            data={"reported_category": "other"},
            files={"image": ("pothole.jpg", make_test_image_bytes(), "image/jpeg")},
        )
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "Inconclusive"
    assert resp.json()["scoring_weight"] == 0.0


def test_no_detections_returns_inconclusive():
    with patch("app.evidence_router.get_model", return_value=make_mock_model([])):
        resp = client.post(
            "/api/evidence/analyze",
            data={"reported_category": "road_damage"},
            files={"image": ("blank.jpg", make_test_image_bytes(), "image/jpeg")},
        )
    assert resp.status_code == 200
    assert resp.json() == {"verdict": "Inconclusive", "detections": [], "scoring_weight": 0.0}


def test_invalid_image_returns_400():
    resp = client.post(
        "/api/evidence/analyze",
        data={"reported_category": "road_damage"},
        files={"image": ("not_an_image.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.skipif(not WEIGHTS_PATH.exists(), reason="weights/best.pt not present")
def test_real_model_inference_smoke():
    """Runs real YOLO inference on a blank image to verify best.pt loads and predicts cleanly."""
    resp = client.post(
        "/api/evidence/analyze",
        data={"reported_category": "road_damage"},
        files={"image": ("blank.jpg", make_test_image_bytes(), "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] in {"Visual Match", "Mismatch", "Inconclusive"}
    assert body["scoring_weight"] == 0.0
