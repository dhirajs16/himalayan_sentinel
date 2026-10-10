from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RiskFactors(BaseModel):
    rainfall_score: float = Field(ge=0, le=100)
    river_level_score: float = Field(ge=0, le=100)
    glacial_risk_score: float = Field(ge=0, le=100)
    community_report_score: float = Field(ge=0, le=100)
    population_exposure_score: float = Field(ge=0, le=100)


class CommunityReport(BaseModel):
    region: str
    report_type: Literal[
        "sudden_river_rise",
        "landslide",
        "blocked_road",
        "damaged_bridge",
        "unusual_water_color",
        "other",
    ]
    description: str = Field(min_length=5, max_length=500)
    urgency: Literal["low", "medium", "high"]
    location: str | None = None


class StoredReport(CommunityReport):
    id: int
    created_at: datetime


class AIRequest(BaseModel):
    region_id: str
    language: Literal["en", "ne"] = "en"
