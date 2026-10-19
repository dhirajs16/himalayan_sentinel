from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(StrictModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class Review(StrictModel):
    action: Literal["escalate", "reject", "request_verification", "confirm"]
    reason: str = Field(min_length=5, max_length=2000)
    severity: Literal["Low", "Moderate", "High", "Critical"] = "High"


class AlertDraft(StrictModel):
    incident_id: str
    title: str = Field(min_length=5, max_length=160)
    disaster_type: Literal["Flood", "GLOF", "Landslide", "Other"] = "Flood"
    severity: Literal["Low", "Moderate", "High", "Critical"] = "High"
    description: str = Field(min_length=10, max_length=4000)
    evidence_summary: str = Field(min_length=5, max_length=2000)
    safety_instructions: str = Field(min_length=10, max_length=3000)
    resources: list[str] = Field(default_factory=list, max_length=20)
    effective_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_times(self):
        if not self.effective_at.tzinfo or not self.expires_at.tzinfo:
            raise ValueError("Use timezone-aware alert times")
        if self.expires_at <= self.effective_at or self.expires_at <= datetime.now(UTC):
            raise ValueError("Expiry must follow effective time and be in the future")
        return self


class AlertAction(StrictModel):
    reason: str = Field(min_length=5, max_length=2000)


class UserUpdate(StrictModel):
    active: bool
    jurisdictions: list[str] = Field(max_length=100)


class UserCreate(Login):
    role: Literal["admin", "government"]
    jurisdictions: list[str] = Field(default_factory=list, max_length=100)


class SettingUpdate(StrictModel):
    low_max: float = Field(ge=0, le=98)
    moderate_max: float = Field(ge=1, le=99)
    high_max: float = Field(ge=2, le=100)

    @model_validator(mode="after")
    def order(self):
        if not self.low_max < self.moderate_max < self.high_max:
            raise ValueError("Thresholds must be increasing")
        return self


class TemplateUpdate(StrictModel):
    safety_instructions: str = Field(min_length=10, max_length=3000)


class IncidentUpdate(StrictModel):
    status: Literal["Confirmed", "Responding", "Resolved"]
    actions: list[str] = Field(max_length=20)
    reason: str = Field(min_length=5, max_length=2000)
