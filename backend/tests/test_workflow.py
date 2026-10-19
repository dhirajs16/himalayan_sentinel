import asyncio
import hashlib
import io
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from PIL import Image

from app import db
from app.config import settings
from app.jobs import maintenance, sync_weather
from app.providers import AIExplanationProvider, WeatherProvider
from app.risk_engine import assess_lake


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (12, 12), "blue").save(output, "PNG")
    return output.getvalue()


def report(
    client, description="Observed unusual river rise near the crossing.", **changes
):
    data = {
        "region": "rasuwa",
        "category": "sudden_river_rise",
        "description": description,
        "lat": 28.156,
        "lng": 85.329,
        "observed_at": datetime.now(UTC).isoformat(),
        "consent": "true",
        "accuracy": "true",
        "demo_verified": "true",
        "contact": "PRIVATE@example.test",
    }
    data.update(changes)
    return client.post(
        "/api/v1/reports",
        data=data,
        files={"image": ("../../evidence.png", image_bytes(), "image/png")},
    )


def confirmed(system, auth):
    created = report(system)
    assert created.status_code == 201, created.text
    identifier = created.json()["id"]
    assert (
        system.post(
            f"/api/v1/admin/reports/{identifier}/review",
            headers=auth("admin"),
            json={"action": "escalate", "reason": "Image reviewed for demo"},
        ).status_code
        == 200
    )
    response = system.post(
        f"/api/v1/government/reports/{identifier}/review",
        headers=auth("official"),
        json={
            "action": "confirm",
            "reason": "Field evidence confirmed in demonstration",
        },
    )
    assert response.status_code == 200, response.text
    return created.json(), response.json()["incident_id"]


def alert_payload(incident_id):
    return {
        "incident_id": incident_id,
        "title": "River monitoring demo notice",
        "disaster_type": "Flood",
        "severity": "High",
        "description": "A reviewed local observation supports increased monitoring.",
        "evidence_summary": "Confirmed demo observation.",
        "safety_instructions": "Follow official local instructions and avoid riverbanks.",
        "resources": [],
        "effective_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }


def test_complete_citizen_to_public_alert_and_resolution(system, auth):
    submission, incident_id = confirmed(system, auth)
    staff = auth("official")
    created = system.post(
        "/api/v1/government/alerts", headers=staff, json=alert_payload(incident_id)
    )
    assert created.status_code == 201, created.text
    identifier = created.json()["id"]
    path = f"/api/v1/government/alerts/{identifier}"
    assert system.get("/api/v1/public/alerts").json()["total"] == 0
    assert (
        system.post(
            path + "/publish", headers=staff, json={"reason": "Premature publication"}
        ).status_code
        == 409
    )
    for action in ["submit", "approve", "publish"]:
        response = system.post(
            path + "/" + action,
            headers=staff,
            json={"reason": "Reviewed for local demonstration"},
        )
        assert response.status_code == 200, response.text
    public = system.get("/api/v1/public/alerts").json()
    assert public["items"][0]["title"] == "River monitoring demo notice"
    assert public["items"][0]["is_demo"] is True
    assert "approved_by" not in public["items"][0]
    assert (
        system.get("/api/v1/reports/" + submission["tracking_id"]).json()["status"]
        == "Verified"
    )
    deliveries = system.get("/api/v1/admin/deliveries", headers=auth("admin")).json()[
        "items"
    ]
    assert len(deliveries) == 3
    assert all(d["status"] == "mock_delivered" for d in deliveries)
    assert (
        system.post(
            path + "/publish", headers=staff, json={"reason": "Duplicate publication"}
        ).status_code
        == 409
    )
    assert (
        system.post(
            path + "/resolve", headers=staff, json={"reason": "Demo situation resolved"}
        ).status_code
        == 200
    )
    assert system.get("/api/v1/public/alerts").json()["total"] == 0
    assert (
        system.patch(
            f"/api/v1/government/incidents/{incident_id}",
            headers=staff,
            json={"status": "Resolved", "actions": [], "reason": "Response completed"},
        ).status_code
        == 200
    )
    events = system.get("/api/v1/admin/audit-logs", headers=auth("admin")).json()[
        "items"
    ]
    assert {
        "report.submitted",
        "report.escalate",
        "report.confirm",
        "alert.approve",
        "alert.publish",
        "alert.resolve",
    } <= {e["action"] for e in events}
    assert "PRIVATE@example.test" not in str(events)


def test_roles_and_jurisdictions_enforced_on_server(system, auth):
    response = report(system)
    identifier = response.json()["id"]
    assert system.get("/api/v1/admin/reports").status_code == 401
    assert (
        system.get("/api/v1/admin/reports", headers=auth("official")).status_code == 403
    )
    assert (
        system.get("/api/v1/government/reports", headers=auth("admin")).status_code
        == 403
    )
    assert (
        system.post(
            f"/api/v1/admin/reports/{identifier}/review",
            headers=auth("admin"),
            json={"action": "confirm", "reason": "Admin cannot confirm"},
        ).status_code
        == 422
    )
    assert (
        system.post(
            f"/api/v1/government/reports/{identifier}/review",
            headers=auth("official"),
            json={"action": "confirm", "reason": "Not moderated yet"},
        ).status_code
        == 409
    )
    assert (
        system.get(
            f"/api/v1/staff/reports/{identifier}/media", headers=auth("other")
        ).status_code
        == 403
    )
    assert (
        system.post(
            f"/api/v1/government/reports/{identifier}/review",
            headers=auth("other"),
            json={"action": "confirm", "reason": "Outside jurisdiction"},
        ).status_code
        == 403
    )
    assert (
        system.get("/api/v1/government/reports", headers=auth("other")).json()["total"]
        == 0
    )


def test_reports_private_tracking_and_sanitized_media(system, auth):
    response = report(system)
    assert response.status_code == 201
    body = response.json()
    assert "contact" not in str(body)
    assert system.get("/reports").status_code == 410
    assert system.get("/api/v1/reports/" + body["id"]).status_code == 404
    assert report(system).status_code == 409
    media = system.get(
        f"/api/v1/staff/reports/{body['id']}/media", headers=auth("admin")
    )
    assert media.status_code == 200
    assert media.headers["cache-control"] == "no-store"
    assert not Image.open(io.BytesIO(media.content)).getexif()
    assert all(p.parent == settings.storage_dir for p in settings.storage_dir.iterdir())
    with db.transaction() as conn:
        row = db.rows(conn, db.reports)[0]
        assert row["tracking_hash"] != body["tracking_id"]


@pytest.mark.parametrize(
    "changes",
    [
        {"lat": 1},
        {"consent": "false"},
        {"demo_verified": "false"},
        {"observed_at": "2020-01-01T00:00:00Z"},
        {"category": "invented"},
        {"region": "elsewhere"},
    ],
)
def test_report_validation(system, changes):
    assert report(system, **changes).status_code == 422


def test_invalid_upload_and_limits(system):
    data = {
        "region": "rasuwa",
        "category": "other",
        "description": "A long enough observation",
        "lat": 28.156,
        "lng": 85.329,
        "observed_at": datetime.now(UTC).isoformat(),
        "consent": "true",
        "accuracy": "true",
        "demo_verified": "true",
    }
    assert (
        system.post(
            "/api/v1/reports",
            data=data,
            files={"image": ("x.png", b"not an image", "image/png")},
        ).status_code
        == 415
    )
    assert (
        system.post(
            "/api/v1/reports",
            data=data,
            files={"image": ("x.svg", b"<svg/>", "image/svg+xml")},
        ).status_code
        == 415
    )
    assert (
        system.post(
            "/api/v1/reports",
            data=data,
            files={"image": ("x.png", b"a" * (5 * 1024 * 1024 + 1), "image/png")},
        ).status_code
        == 413
    )
    assert not settings.storage_dir.exists()


def test_report_rate_limit(system):
    for i in range(5):
        assert (
            report(system, description=f"Different observation number {i}").status_code
            == 201
        )
    assert report(system, description="Sixth distinct observation").status_code == 429


def test_session_refresh_rotation_logout_and_origin(system, auth):
    original = auth("admin")
    cookie = system.cookies.get("sentinel_refresh")
    assert (
        system.post(
            "/api/v1/auth/refresh", headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    response = system.post(
        "/api/v1/auth/refresh", headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"] != original["Authorization"].split()[1]
    assert system.get("/api/v1/auth/me", headers=original).status_code == 401
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    assert system.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert system.get("/api/v1/auth/me", headers=headers).status_code == 401
    system.cookies.set("sentinel_refresh", cookie)
    assert (
        system.post(
            "/api/v1/auth/refresh", headers={"Origin": "http://localhost:3000"}
        ).status_code
        == 401
    )


def test_alert_edit_invalidates_approval_and_history(system, auth):
    _, incident = confirmed(system, auth)
    staff = auth("official")
    payload = alert_payload(incident)
    identifier = system.post(
        "/api/v1/government/alerts", headers=staff, json=payload
    ).json()["id"]
    path = "/api/v1/government/alerts/" + identifier
    for action in ("submit", "approve"):
        assert (
            system.post(
                path + "/" + action, headers=staff, json={"reason": "Reviewed evidence"}
            ).status_code
            == 200
        )
    assert (
        system.put(
            path, headers=staff, json={**payload, "title": "Updated monitoring draft"}
        ).status_code
        == 200
    )
    assert (
        system.post(
            path + "/publish",
            headers=staff,
            json={"reason": "Approval was invalidated"},
        ).status_code
        == 409
    )
    assert len(system.get(path + "/history", headers=staff).json()["items"]) == 4
    assert (
        system.post(
            path + "/approve", headers=auth("admin"), json={"reason": "Not authorized"}
        ).status_code
        == 403
    )


def test_risk_components_missingness_and_boundaries():
    baseline = assess_lake({"rank": "I"})
    wet = assess_lake({"rank": "I"}, {"forecast_rainfall_mm": 150, "mode": "simulated"})
    assert baseline["overall_monitoring_priority"]["score"] == 35
    assert wet["overall_monitoring_priority"]["score"] == 55
    assert wet["evidence_confidence"] <= 25
    assert wet["completeness"] == 55
    assert sum(c["contribution"] for c in wet["components"]) == 55
    assert (
        next(c for c in wet["components"] if c["key"] == "population")["status"]
        == "missing"
    )
    assert assess_lake({"rank": "Unknown"})["baseline_hazard"]["score"] is None
    assert (
        assess_lake({"rank": "I"}, {"forecast_rainfall_mm": -20})[
            "overall_monitoring_priority"
        ]["score"]
        == 35
    )


def test_provider_failure_caching_and_ai_fallback(system, monkeypatch):
    monkeypatch.setattr(settings, "weather_live", True)

    async def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "get", fail)
    location = {"id": "lake", "lat": 28, "lng": 85}
    result = asyncio.run(WeatherProvider().fetch(location))
    assert result["mode"] == "simulated"
    assert result["last_success"] is None
    with db.transaction() as conn:
        conn.execute(
            db.observations.insert().values(
                id="cached",
                location_id="lake",
                created_at="2020-01-01T00:00:00+00:00",
                payload={**result, "mode": "live"},
            )
        )
    result = asyncio.run(WeatherProvider().fetch(location))
    assert result["mode"] == "cached" and result["freshness"] == "stale"
    monkeypatch.setattr(settings, "gemini_api_key", "test-not-real")
    monkeypatch.setattr(httpx.AsyncClient, "post", fail)
    draft = asyncio.run(AIExplanationProvider().explain({"evidence_ids": ["source"]}))
    assert draft["source"] == "deterministic-template" and draft["status"] == "Draft"
    assert "score" not in draft


def test_cached_simulation_never_becomes_live_evidence(system):
    fixture = WeatherProvider().fixture()
    with db.transaction() as conn:
        conn.execute(
            db.observations.insert().values(
                id="simulation", location_id="demo", payload=fixture
            )
        )
    payload = asyncio.run(WeatherProvider().fetch({"id": "demo", "lat": 28, "lng": 85}))
    assert payload["mode"] == "simulated"
    assert payload["freshness"] == "demo"


def test_job_persists_components_idempotently(system):
    with db.transaction() as conn:
        conn.execute(
            db.lakes.insert().values(
                id="lake",
                source_id="source",
                lat=28,
                lng=85,
                properties={"rank": "I"},
                geometry={"type": "Point", "coordinates": [85, 28]},
            )
        )
    asyncio.run(sync_weather())
    asyncio.run(sync_weather())
    with db.transaction() as conn:
        records = db.rows(conn, db.assessments)
        assert len(records) == 1
        assert len(records[0]["assessment"]["components"]) == 10
    maintenance()
    assert system.get("/api/v1/public/lakes").json()["total"] == 1
    assert system.get("/health/database").json()["status"] == "ok"


def test_migrations_and_seed_are_idempotent(system, monkeypatch):
    from app.scripts.seed_demo import seed

    monkeypatch.setattr(settings, "admin_email", "admin@example.test")
    monkeypatch.setattr(settings, "admin_password", "UnusedPassword123")
    monkeypatch.setattr(settings, "government_email", "official@example.test")
    monkeypatch.setattr(settings, "government_password", "UnusedPassword123")
    seed()
    seed()
    db.migrate()
    with db.transaction() as conn:
        assert len(db.rows(conn, db.users)) == 3


def test_optional_local_dataset_import_is_reproducible(system):
    import sys
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(scripts))
    from import_geospatial_data import import_data

    raw = list((scripts.parents[1] / "data").rglob("PDGLs.shp"))
    if not raw:
        pytest.skip("Local licensed ICIMOD data not installed")
    before = hashlib.sha256(raw[0].read_bytes()).hexdigest()
    import_data()
    import_data()
    assert hashlib.sha256(raw[0].read_bytes()).hexdigest() == before
    lakes = system.get("/api/v1/public/lakes").json()["items"]
    assert len(lakes) == 47
    assert {l["properties"]["country"] for l in lakes} == {"Nepal", "China", "India"}


def test_published_revision_stays_visible_until_reapproved(system, auth):
    _, incident = confirmed(system, auth)
    staff = auth("official")
    payload = alert_payload(incident)
    identifier = system.post(
        "/api/v1/government/alerts", headers=staff, json=payload
    ).json()["id"]
    path = "/api/v1/government/alerts/" + identifier
    for action in ("submit", "approve", "publish"):
        assert (
            system.post(
                path + "/" + action, headers=staff, json={"reason": "Evidence reviewed"}
            ).status_code
            == 200
        )
    assert (
        system.post(
            path + "/acknowledge",
            headers=staff,
            json={"reason": "Response team acknowledged"},
        ).status_code
        == 200
    )
    updated = {**payload, "title": "Revised public notice after review"}
    assert system.put(path, headers=staff, json=updated).status_code == 200
    assert (
        system.get("/api/v1/public/alerts").json()["items"][0]["title"]
        == payload["title"]
    )
    for action in ("submit", "approve", "publish"):
        assert (
            system.post(
                path + "/" + action,
                headers=staff,
                json={"reason": "Revised evidence reviewed"},
            ).status_code
            == 200
        )
    public = system.get("/api/v1/public/alerts").json()["items"][0]
    assert public["title"] == updated["title"] and public["status"] == "Updated"


def test_expired_and_future_alerts_not_public(system, auth):
    _, incident = confirmed(system, auth)
    staff = auth("official")
    payload = alert_payload(incident)
    payload["effective_at"] = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    identifier = system.post(
        "/api/v1/government/alerts", headers=staff, json=payload
    ).json()["id"]
    path = "/api/v1/government/alerts/" + identifier
    for action in ("submit", "approve", "publish"):
        system.post(
            path + "/" + action,
            headers=staff,
            json={"reason": "Future notice scheduled"},
        )
    assert system.get("/api/v1/public/alerts").json()["total"] == 0
    with db.transaction() as conn:
        conn.execute(
            db.alerts.update()
            .where(db.alerts.c.id == identifier)
            .values(
                effective_at="2020-01-01T00:00:00+00:00",
                expires_at="2020-01-02T00:00:00+00:00",
            )
        )
    maintenance()
    assert (
        system.get("/api/v1/government/alerts", headers=staff).json()["items"][0][
            "status"
        ]
        == "Expired"
    )
    assert system.get("/api/v1/public/alerts").json()["total"] == 0
