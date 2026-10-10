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
    return {**region, "risk": calculate_risk(factors)}
