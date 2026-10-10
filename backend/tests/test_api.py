from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_regions_have_transparent_risk():
    regions = client.get("/regions").json()
    assert len(regions) == 8
    assert regions[0]["risk"]["weights"]["rainfall_score"] == 0.30


def test_calculation_boundaries():
    payload = {
        "rainfall_score": 100,
        "river_level_score": 100,
        "glacial_risk_score": 100,
        "community_report_score": 100,
        "population_exposure_score": 100,
    }
    assert client.post("/risk/calculate", json=payload).json()["level"] == "Critical"
