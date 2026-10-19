import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .context_api import router as context_router
from .district_weather import router as district_weather_router
from .risk_engine import calculate_risk, enrich_region
from .schemas import AIRequest, CommunityReport, RiskFactors, StoredReport
from .workflow import initialize, router

DISCLAIMER = "This is a decision-support estimate, not an official disaster warning."
DATA_PATH = Path(__file__).parent / "data" / "regions.json"
REGIONS = json.loads(DATA_PATH.read_text(encoding="utf-8"))


@asynccontextmanager
async def lifespan(app):
    initialize()
    yield


app = FastAPI(title="Himalayan Sentinel API", version="1.0.0", lifespan=lifespan)
app.include_router(router)
app.include_router(district_weather_router)
app.include_router(context_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def secure_headers(request, call_next):
    # Reject oversized multipart bodies before Starlette buffers them.
    length = request.headers.get("content-length")
    if (
        request.method == "POST"
        and request.url.path == "/api/v1/reports"
        and not length
    ):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {"detail": "Content-Length required for evidence uploads"}, status_code=411
        )
    if length and (not length.isdigit() or int(length) > 6 * 1024 * 1024):
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=()"
    if (
        "/auth/" in request.url.path
        or "/admin/" in request.url.path
        or "/government/" in request.url.path
        or "/reports" in request.url.path
    ):
        response.headers["Cache-Control"] = "no-store"
    return response


def get_region(region_id: str) -> dict:
    region = next((item for item in REGIONS if item["id"] == region_id), None)
    if not region:
        raise HTTPException(404, "Region not found")
    return enrich_region(region)


@app.get("/health")
def health():
    return {"status": "ok", "service": "himalayan-sentinel"}


@app.get("/health/database")
def database_health():
    from sqlalchemy import text

    from . import db

    with db.transaction() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": db.engine.dialect.name}


@app.get("/health/providers")
def providers_health():
    from . import db

    with db.transaction() as conn:
        return {
            "providers": [
                {
                    "id": r["id"],
                    "mode": r["state"].get("mode"),
                    "health": r["state"].get("health"),
                    "enabled": r["enabled"],
                }
                for r in db.rows(conn, db.sources)
            ]
        }


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
    from .providers import WeatherProvider

    return await WeatherProvider().fetch(selected)


@app.post("/reports", response_model=StoredReport, status_code=201)
def submit_report(report: CommunityReport):
    raise HTTPException(410, "Use /api/v1/reports for verified guest submissions")


@app.get("/reports", response_model=list[StoredReport])
def reports():
    raise HTTPException(
        410, "Reports are private; use authenticated moderation endpoints"
    )


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
        "mode": "simulated",
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
