"""Current forecasts for geographic district context; never a hazard prediction."""

from fastapi import APIRouter, HTTPException, Request

from .context_data import store
from .providers import WeatherProvider
from .security import throttle

router = APIRouter(prefix="/api/v1/public/context")


def district_location(district):
    if not store.districts():
        raise HTTPException(503, "District boundaries unavailable")
    if len(district) > 80:
        raise HTTPException(422, "District name is too long")
    location = store.district(district)
    if not location:
        raise HTTPException(404, "District not found")
    return {**location, "id": "district:" + location["id"]}


@router.get("/weather/{district}")
async def district_weather(district: str, request: Request):
    throttle(request, "district-weather", 60, 300)
    location = district_location(district)
    payload = await WeatherProvider().fetch(location)
    return {
        **payload,
        "district": location["name"],
        "location": {"lat": location["lat"], "lng": location["lng"]},
        "limitations": "Forecast at a representative district location; not observed river flow, district-wide measurement or a flood prediction.",
    }
