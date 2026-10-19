"""Explicit synthetic indicator changes on an imported Rank I source lake."""

import argparse

from sqlalchemy import select

from app import db
from app.config import settings
from app.providers import WeatherProvider
from app.risk_engine import assess_lake


def scenario(phase):
    if settings.environment != "development":
        raise RuntimeError("Demo scenario is development-only")
    db.migrate()
    with db.transaction() as conn:
        lake = next(
            (
                l
                for l in db.rows(conn, db.lakes)
                if l["properties"].get("rank") == "I"
                and l["properties"].get("country") == "Nepal"
            ),
            None,
        )
        if not lake:
            raise RuntimeError(
                "Import licensed ICIMOD PDGL data before running this scenario"
            )
        rain = 0 if phase == "baseline" else 150
        observation = WeatherProvider().fixture(
            "Explicit demo scenario; not observed weather"
        )
        observation["daily"]["precipitation_sum"] = [rain, rain, 70, 40, 20, 10, 0]
        assessment = assess_lake(
            lake["properties"],
            {
                "forecast_rainfall_mm": rain,
                "recent_rainfall_mm": rain,
                "mode": "simulated",
                "freshness": "demo",
                "source_observation_time": "2026-10-10",
            },
        )
        latest = conn.execute(
            select(db.assessments.c.assessment)
            .where(db.assessments.c.lake_id == lake["id"])
            .order_by(db.assessments.c.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if (
            not latest
            or latest["overall_monitoring_priority"]
            != assessment["overall_monitoring_priority"]
        ):
            conn.execute(
                db.assessments.insert().values(
                    id=db.uid(), lake_id=lake["id"], assessment=assessment
                )
            )
            conn.execute(
                db.observations.insert().values(
                    id=db.uid(), location_id=lake["id"], payload=observation
                )
            )
            db.record(
                conn,
                None,
                "demo." + phase,
                lake["id"],
                {"mode": "simulated", "rainfall_mm": rain},
            )
    print(
        f"{lake['id']}: {phase} -> {assessment['overall_monitoring_priority']} (SIMULATED)"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["baseline", "rainfall"], required=True)
    scenario(parser.parse_args().phase)
