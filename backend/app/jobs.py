"""Run `python -m app.jobs --once` or keep running for a 30-minute scheduler."""

import argparse
import asyncio
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import select

from . import db
from .providers import WeatherProvider
from .risk_engine import assess_lake


async def sync_weather():
    with db.transaction() as conn:
        lakes = db.rows(conn, db.lakes)
        thresholds = conn.execute(
            select(db.config.c.value).where(db.config.c.id == "thresholds")
        ).scalar_one_or_none()
    statuses, health = [], []
    for lake in lakes:
        payload = await WeatherProvider().fetch(lake)
        statuses.append(payload["mode"])
        health.append(payload["health"])
        rain = payload["daily"]["precipitation_sum"]
        today = (
            datetime.now(timezone(timedelta(hours=5, minutes=45))).date().isoformat()
        )
        days = payload["daily"]["time"]
        # Around Nepal midnight a recent cached forecast can begin yesterday.
        daily_rain = rain[days.index(today)] if today in days else None
        indicators = {
            "forecast_rainfall_mm": daily_rain,
            "mode": payload["mode"],
            "freshness": payload["freshness"],
            "source_observation_time": today
            if today in days
            else payload["source_observation_time"],
        }
        assessment = assess_lake(lake["properties"], indicators, thresholds)
        with db.transaction() as conn:
            latest = conn.execute(
                select(db.assessments.c.assessment)
                .where(db.assessments.c.lake_id == lake["id"])
                .order_by(db.assessments.c.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            # Avoid duplicate assessment records when rerun without new observations/rules.
            comparable = lambda x: {k: v for k, v in x.items() if k != "assessed_at"}
            if latest is None or comparable(latest) != comparable(assessment):
                conn.execute(
                    db.assessments.insert().values(
                        id=db.uid(), lake_id=lake["id"], assessment=assessment
                    )
                )
    modes = sorted(set(statuses))
    result = {
        "locations": len(lakes),
        "modes": modes,
        "status": "demo"
        if "simulated" in modes
        else "degraded"
        if "degraded" in health
        else "ok",
    }
    with db.transaction() as conn:
        conn.execute(
            db.sync_runs.insert().values(
                id=db.uid(), provider="weather", status=result["status"], details=result
            )
        )
        if lakes:
            state = {
                **payload,
                "locations": len(lakes),
                "modes": modes,
                "health": result["status"],
            }
            conn.execute(
                db.sources.update()
                .where(db.sources.c.id == "weather")
                .values(state=state)
            )
    return result


def maintenance():
    with db.transaction() as conn:
        for alert in db.rows(conn, db.alerts):
            if (
                alert["status"]
                in {"Published", "Updated", "Approved", "Pending approval"}
                and alert["expires_at"] <= db.now()
            ):
                conn.execute(
                    db.alerts.update()
                    .where(db.alerts.c.id == alert["id"])
                    .values(status="Expired", updated_at=db.now())
                )
                db.record(conn, None, "alert.expired", alert["id"])
        for source in db.rows(conn, db.sources):
            state = source["state"]
            if (
                state.get("last_success")
                and (
                    datetime.now(UTC) - datetime.fromisoformat(state["last_success"])
                ).total_seconds()
                > 7200
            ):
                conn.execute(
                    db.sources.update()
                    .where(db.sources.c.id == source["id"])
                    .values(state={**state, "freshness": "stale", "health": "degraded"})
                )
        conn.execute(
            db.limits.delete().where(
                db.limits.c.window < int(datetime.now(UTC).timestamp()) - 86400
            )
        )
        conn.execute(
            db.sessions.delete().where(
                db.sessions.c.refresh_expires < datetime.now(UTC).timestamp()
            )
        )


async def main(once=False):
    from .workflow import initialize

    initialize()
    while True:
        await sync_weather()
        maintenance()
        if once:
            break
        await asyncio.sleep(1800)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    asyncio.run(main(parser.parse_args().once))
