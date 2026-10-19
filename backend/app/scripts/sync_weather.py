"""Verify and persist a district forecast without running a full lake refresh."""

import argparse
import asyncio
import json

from app.district_weather import district_location
from app.providers import WeatherProvider
from app.workflow import initialize


async def sync(district):
    initialize()
    location = district_location(district)
    result = await WeatherProvider().fetch(location, force=True)
    print(
        json.dumps(
            {
                "district": location["name"],
                "mode": result["mode"],
                "freshness": result["freshness"],
                "retrieved_at": result.get("retrieved_at"),
                "source_observation_time": result["source_observation_time"],
                "error": result.get("error"),
                "daily": result["daily"],
            },
            indent=2,
        )
    )
    return result["mode"] == "live"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", default="rasuwa")
    args = parser.parse_args()
    raise SystemExit(0 if asyncio.run(sync(args.district)) else 1)
