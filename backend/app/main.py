import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .risk_engine import calculate_risk, enrich_region
from .schemas import AIRequest, CommunityReport, RiskFactors, StoredReport

DISCLAIMER = "This is a decision-support estimate, not an official disaster warning."
DATA_PATH = Path(__file__).parent / "data" / "regions.json"
REGIONS = json.loads(DATA_PATH.read_text(encoding="utf-8"))
REPORTS: list[StoredReport] = []

app = FastAPI(title="Himalayan Sentinel API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_region(region_id: str) -> dict:
    region = next((item for item in REGIONS if item["id"] == region_id), None)
    if not region:
        raise HTTPException(404, "Region not found")
    return enrich_region(region)


@app.get("/health")
def health():
    return {"status": "ok", "service": "himalayan-sentinel"}


@app.get("/regions")
def regions():
    return [enrich_region(item) for item in REGIONS]


@app.get("/regions/{region_id}")
def region(region_id: str):
    return get_region(region_id)


@app.get("/risk/latest")
def latest_risk():
    return sorted(
        (enrich_region(item) for item in REGIONS),
        key=lambda item: item["risk"]["score"],
        reverse=True,
    )


@app.post("/risk/calculate")
def calculate(factors: RiskFactors):
    return calculate_risk(factors.model_dump())


@app.get("/weather/{region_id}")
async def weather(region_id: str):
    selected = get_region(region_id)
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": selected["lat"],
                "longitude": selected["lng"],
                "daily": "precipitation_sum",
                "forecast_days": 7,
                "timezone": "Asia/Kathmandu",
            },
        )
        response.raise_for_status()
    return response.json()


@app.post("/reports", response_model=StoredReport, status_code=201)
def submit_report(report: CommunityReport):
    stored = StoredReport(
        id=len(REPORTS) + 1, created_at=datetime.now(UTC), **report.model_dump()
    )
    REPORTS.append(stored)
    return stored


@app.get("/reports", response_model=list[StoredReport])
def reports():
    return list(reversed(REPORTS))


def plain_explanation(selected: dict, language: str) -> str:
    score = selected["risk"]["score"]
    if language == "ne":
        return f"{selected['name']} मा जोखिम स्तर {selected['risk']['level']} ({score}/100) छ। पछिल्लो वर्षा, नदीको बढ्दो सतह र हिमतालसम्बन्धी जोखिम मुख्य कारण हुन्। स्थानीय सूचनामा ध्यान दिनुहोस् र सुरक्षित मार्ग तयार राख्नुहोस्। यो निर्णय-सहयोग अनुमान हो, आधिकारिक विपद् चेतावनी होइन।"
    return f"{selected['name']} is currently rated {selected['risk']['level']} ({score}/100). Recent rainfall, the {selected['river_status'].lower()} river condition, and {selected['glacial_risk'].lower()} glacial context are the main drivers. Monitor official updates and keep a safe route ready. {DISCLAIMER}"


@app.post("/ai/explain-risk")
async def explain_risk(request: AIRequest):
    selected = get_region(request.region_id)
    return {
        "region_id": request.region_id,
        "language": request.language,
        "explanation": plain_explanation(selected, request.language),
        "source": "deterministic-fallback",
        "disclaimer": DISCLAIMER,
    }


@app.post("/ai/generate-alert")
async def generate_alert(request: AIRequest):
    selected = get_region(request.region_id)
    level = selected["risk"]["level"]
    if request.language == "ne":
        sms = f"सतर्कता: {selected['name']} मा {level} जोखिम। नदी किनारबाट टाढा रहनुहोस्, स्थानीय सूचना सुन्नुहोस् र सुरक्षित मार्ग तयार राख्नुहोस्। आधिकारिक चेतावनी होइन।"
        checklist = [
            "फोन चार्ज गर्नुहोस्",
            "पानी र औषधि तयार राख्नुहोस्",
            "परिवारको सुरक्षित मार्ग तय गर्नुहोस्",
            "आधिकारिक सूचना सुन्नुहोस्",
        ]
    else:
        sms = f"ADVISORY: {level} flood-risk estimate for {selected['name']}. Stay away from riverbanks, follow local updates, and prepare a safe route. Not an official warning."
        checklist = [
            "Charge phones and power banks",
            "Pack water and essential medicine",
            "Agree on a family evacuation route",
            "Follow official local authority updates",
        ]
    return {
        "region_id": request.region_id,
        "language": request.language,
        "sms": sms,
        "municipality_notice": plain_explanation(selected, request.language),
        "checklist": checklist,
        "disclaimer": DISCLAIMER,
    }
