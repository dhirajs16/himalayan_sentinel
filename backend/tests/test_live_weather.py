import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app import db
from app.config import settings
from app.providers import WeatherDaily, WeatherProvider


def forecast():
    today = datetime.now(timezone(timedelta(hours=5, minutes=45))).date()
    return {
        "time": [(today + timedelta(days=i)).isoformat() for i in range(2)],
        "precipitation_sum": [1.5, None],
        "temperature_2m_max": [12, 13],
    }


def test_live_forecast_is_persisted_then_cached(system, monkeypatch):
    monkeypatch.setattr(settings, "weather_live", True)
    monkeypatch.setattr(WeatherProvider, "rate_limited_until", 0)
    calls = []

    async def success(self, url, **kwargs):
        calls.append(kwargs["params"])
        return httpx.Response(
            200, json={"daily": forecast()}, request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", success)
    first = system.get("/api/v1/public/context/weather/rasuwa").json()
    second = system.get("/api/v1/public/context/weather/rasuwa").json()
    assert first["mode"] == "live" and first["kind"] == "forecast"
    assert second["mode"] == "cached" and second["freshness"] == "fresh"
    assert second["retrieved_at"] == first["retrieved_at"]
    assert len(calls) == 1
    assert "Representative" not in first["district"]
    with db.transaction() as conn:
        stored = db.rows(conn, db.observations)
        assert len(stored) == 1 and stored[0]["location_id"] == "district:rasuwa"
        state = conn.execute(
            select(db.sources.c.state).where(db.sources.c.id == "weather")
        ).scalar_one()
        assert state["mode"] == "cached" and state["last_success"]
    assert (
        system.get("/api/v1/public/context/weather/no-such-district").status_code == 404
    )


def test_disabled_provider_never_reuses_fresh_live_cache(system, monkeypatch):
    monkeypatch.setattr(settings, "weather_live", True)
    location = {"id": "location", "lat": 28, "lng": 85}
    with db.transaction() as conn:
        conn.execute(
            db.observations.insert().values(
                id="prior",
                location_id="location",
                payload={
                    **WeatherProvider().fixture(),
                    "mode": "live",
                    "daily": forecast(),
                },
            )
        )
        conn.execute(
            db.sources.update()
            .where(db.sources.c.id == "weather")
            .values(enabled=False)
        )

    async def unexpected(*args, **kwargs):
        pytest.fail("Disabled provider attempted an external request")

    monkeypatch.setattr(httpx.AsyncClient, "get", unexpected)
    result = asyncio.run(WeatherProvider().fetch(location))
    assert result["mode"] == "simulated" and result["last_success"] is None


def test_failure_returns_stale_cache_and_throttle_stops_retries(system, monkeypatch):
    monkeypatch.setattr(settings, "weather_live", True)
    monkeypatch.setattr(WeatherProvider, "rate_limited_until", 0)
    with db.transaction() as conn:
        conn.execute(
            db.observations.insert().values(
                id="old",
                location_id="one",
                created_at="2020-01-01T00:00:00+00:00",
                payload={
                    **WeatherProvider().fixture(),
                    "mode": "live",
                    "daily": forecast(),
                },
            )
        )
    requests = []

    async def limited(self, url, **kwargs):
        requests.append(url)
        return httpx.Response(429, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", limited)
    result = asyncio.run(WeatherProvider().fetch({"id": "one", "lat": 28, "lng": 85}))
    assert result["mode"] == "cached" and result["freshness"] == "stale"
    other = asyncio.run(WeatherProvider().fetch({"id": "two", "lat": 28, "lng": 85}))
    assert other["mode"] == "simulated" and len(requests) == 1


@pytest.mark.parametrize(
    "change",
    [
        {"precipitation_sum": [-1, 0]},
        {"temperature_2m_max": [float("nan"), 0]},
        {"time": ["bad-date", "bad-date"]},
        {"time": ["2026-01-01", "2026-01-01"]},
        {"precipitation_sum": [2]},
    ],
)
def test_malformed_forecast_rejected(change):
    with pytest.raises(ValidationError):
        WeatherDaily.model_validate({**forecast(), **change})


@pytest.mark.parametrize("covers_today", [True, False])
def test_assessment_uses_current_nepal_day_or_unknown(
    system, monkeypatch, covers_today
):
    from app.jobs import sync_weather

    today = datetime.now(timezone(timedelta(hours=5, minutes=45))).date()
    days = [
        (today - timedelta(days=1)).isoformat(),
        today.isoformat() if covers_today else (today - timedelta(days=2)).isoformat(),
    ]

    async def cached(self, location, force=False):
        return {
            **WeatherProvider().fixture(),
            "mode": "cached",
            "freshness": "stale",
            "health": "degraded",
            "daily": {"time": days, "precipitation_sum": [150, 0]},
        }

    monkeypatch.setattr(WeatherProvider, "fetch", cached)
    with db.transaction() as conn:
        conn.execute(
            db.lakes.insert().values(
                id="midnight",
                source_id="midnight",
                lat=28,
                lng=85,
                properties={"rank": "I"},
                geometry={"type": "Point", "coordinates": [85, 28]},
            )
        )
    result = asyncio.run(sync_weather())
    assert result["status"] == "degraded"
    with db.transaction() as conn:
        assessment = conn.execute(
            select(db.assessments.c.assessment).where(
                db.assessments.c.lake_id == "midnight"
            )
        ).scalar_one()
    rain = next(
        part for part in assessment["components"] if part["key"] == "forecast_rainfall"
    )
    assert rain["contribution"] == 0
    assert rain["status"] == ("available" if covers_today else "missing")


def test_simultaneous_requests_share_cache_and_bound_concurrency(system, monkeypatch):
    monkeypatch.setattr(settings, "weather_live", True)
    monkeypatch.setattr(WeatherProvider, "rate_limited_until", 0)
    active, peak, calls = 0, 0, []

    async def success(self, url, **kwargs):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        calls.append(kwargs["params"])
        await asyncio.sleep(0.01)
        active -= 1
        return httpx.Response(
            200, json={"daily": forecast()}, request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", success)

    async def run():
        provider = WeatherProvider()
        return await asyncio.gather(
            *[
                provider.fetch({"id": str(index), "lat": 28, "lng": 85})
                for index in [0, 0, 0, 1, 2, 3, 4]
            ]
        )

    results = asyncio.run(run())
    assert len(calls) == 5 and peak <= 3
    assert [item["mode"] for item in results[:3]] == ["live", "cached", "cached"]
