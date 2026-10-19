import typing

WEIGHTS = {
    "rainfall_score": 0.30,
    "river_level_score": 0.25,
    "glacial_risk_score": 0.20,
    "community_report_score": 0.15,
    "population_exposure_score": 0.10,
}


def rainfall_score(rainfall_mm: float) -> float:
    return min(100.0, round(rainfall_mm / 1.5, 1))


def risk_level(score: float) -> str:
    if score <= 25:
        return "Low"
    if score <= 50:
        return "Moderate"
    if score <= 75:
        return "High"
    return "Critical"


def calculate_risk(factors: dict[str, float]) -> dict[str, typing.Any]:
    score = round(sum(factors[key] * weight for key, weight in WEIGHTS.items()), 1)
    return {
        "score": score,
        "level": risk_level(score),
        "factors": factors,
        "weights": WEIGHTS,
    }


def enrich_region(region: dict[str, typing.Any]) -> dict[str, typing.Any]:
    factors = {
        "rainfall_score": rainfall_score(region["rainfall_mm"]),
        "river_level_score": region["river_level_score"],
        "glacial_risk_score": region["glacial_risk_score"],
        "community_report_score": region["community_report_score"],
        "population_exposure_score": region["population_exposure_score"],
    }
    return {
        **region,
        "risk": calculate_risk(factors),
        "mode": "simulated",
        "source_observation_time": "2026-10-10",
    }


ENGINE_VERSION = "lake-rules-1.0"
COMPONENTS = {
    "baseline_hazard": 35,
    "forecast_rainfall": 20,
    "recent_rainfall": 10,
    "temperature_snowmelt": 5,
    "lake_change": 5,
    "terrain": 5,
    "population": 8,
    "infrastructure": 2,
    "verified_reports": 5,
    "official_observations": 5,
}


def assess_lake(properties, indicators=None, thresholds=None):
    """Missing evidence contributes zero AND reduces completeness; never means safe."""
    from datetime import UTC, datetime

    indicators = indicators or {}
    rank = str(properties.get("rank", "")).strip().upper()
    baseline = {"I": 100, "II": 65, "III": 35}.get(rank)
    values = {
        "baseline_hazard": baseline,
        "forecast_rainfall": min(100, max(0, indicators["forecast_rainfall_mm"] / 1.5))
        if indicators.get("forecast_rainfall_mm") is not None
        else None,
        "recent_rainfall": min(100, max(0, indicators["recent_rainfall_mm"] / 1.5))
        if indicators.get("recent_rainfall_mm") is not None
        else None,
        # Temperature alone is not sufficient to infer snowmelt.
        "temperature_snowmelt": indicators.get("temperature_snowmelt_score"),
        "lake_change": indicators.get("lake_change_score"),
        "terrain": indicators.get("terrain_score"),
        "population": indicators.get("population_score"),
        "infrastructure": indicators.get("infrastructure_score"),
        "verified_reports": indicators.get("verified_report_score"),
        "official_observations": indicators.get("official_observation_score"),
    }
    parts = [
        {
            "key": key,
            "value": value,
            "weight": weight,
            "contribution": round(max(0, min(100, value)) * weight / 100, 2)
            if value is not None
            else 0,
            "status": "missing" if value is None else "available",
        }
        for key, weight in COMPONENTS.items()
        for value in [values[key]]
    ]
    score = round(sum(p["contribution"] for p in parts), 2)
    completeness = sum(p["weight"] for p in parts if p["status"] == "available")
    demo = indicators.get("mode") == "simulated"
    stale = indicators.get("freshness") == "stale"
    confidence = min(completeness, 25 if demo else 100, 40 if stale else 100)
    cutoffs = thresholds or {"low_max": 25, "moderate_max": 50, "high_max": 75}
    level = (
        "Low"
        if score <= cutoffs["low_max"]
        else "Moderate"
        if score <= cutoffs["moderate_max"]
        else "High"
        if score <= cutoffs["high_max"]
        else "Critical"
    )
    return {
        "version": ENGINE_VERSION,
        "assessed_at": datetime.now(UTC).isoformat(),
        "baseline_hazard": {"rank": rank or None, "score": baseline},
        "dynamic_environmental_risk": round(
            sum(
                p["contribution"]
                for p in parts
                if p["key"]
                in [
                    "forecast_rainfall",
                    "recent_rainfall",
                    "temperature_snowmelt",
                    "lake_change",
                    "terrain",
                ]
            ),
            2,
        ),
        "exposure_risk": round(
            sum(
                p["contribution"]
                for p in parts
                if p["key"] in ["population", "infrastructure"]
            ),
            2,
        ),
        "evidence_confidence": confidence,
        "completeness": completeness,
        "components": parts,
        "overall_monitoring_priority": {"score": score, "level": level},
        "thresholds": cutoffs,
        "mode": indicators.get("mode", "static"),
        "freshness": indicators.get("freshness", "static"),
        "source_observation_time": indicators.get("source_observation_time"),
        "human_review": "Pending",
        "limitations": "Prototype weights, not scientifically validated. Low completeness does not establish low hazard. Exposure and snowmelt are unknown unless supported by observations.",
    }
