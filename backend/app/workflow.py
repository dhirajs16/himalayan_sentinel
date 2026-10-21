import hashlib
import io
import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import and_, func, select
from sqlalchemy.sql import Select

from . import db
from .boundaries import BOUNDARY_LICENSE, BOUNDARY_SOURCE, boundary_path
from .config import ROOT, settings
from .providers import (
    SAFETY,
    AIExplanationProvider,
    NotificationProvider,
    WeatherProvider,
    provider_states,
)
from .risk_engine import ENGINE_VERSION, assess_lake
from .security import (
    current_user,
    digest,
    hash_password,
    jurisdiction,
    new_session,
    role,
    throttle,
    verify_password,
)
from .workflow_schemas import (
    AlertAction,
    AlertDraft,
    IncidentUpdate,
    Login,
    Review,
    SettingUpdate,
    TemplateUpdate,
    UserCreate,
    UserUpdate,
)

router = APIRouter(prefix="/api/v1")
admin = role("admin")
official = role("government")
REGIONS = json.loads(
    (Path(__file__).parent / "data/regions.json").read_text(encoding="utf-8")
)
REGION_IDS = {r["id"] for r in REGIONS}
Image.MAX_IMAGE_PIXELS = 20_000_000


def find(conn, table, entity_id):
    row = conn.execute(select(table).where(table.c.id == entity_id)).mappings().first()
    if not row:
        raise HTTPException(404, "Record not found")
    return dict(row)


def public_user(user):
    return {
        key: user[key] for key in ("id", "email", "role", "jurisdictions", "active")
    }


def cookie(response, refresh):
    response.set_cookie(
        "sentinel_refresh",
        refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=28800,
        path="/api/v1/auth",
    )


def trusted_origin(request):
    if request.headers.get("origin") not in settings.cors_origins.split(","):
        raise HTTPException(403, "Trusted origin required")


@router.post("/auth/login")
def login(payload: Login, request: Request, response: Response):
    throttle(request, "login", 10, 300)
    with db.transaction() as conn:
        user = (
            conn.execute(
                select(db.users).where(db.users.c.email == payload.email.lower())
            )
            .mappings()
            .first()
        )
        # Always run a password derivation to reduce account enumeration by timing.
        valid = verify_password(
            payload.password,
            user["password_hash"] if user else hash_password("unused-password"),
        )
        if not user or not valid or not user["active"]:
            raise HTTPException(401, "Invalid credentials")
        access, refresh = new_session(conn, user["id"])
        db.record(conn, user["id"], "login", user["id"])
    cookie(response, refresh)
    return {
        "access_token": access,
        "token_type": "bearer",
        "expires_in": 900,
        "user": public_user(user),
    }


@router.post("/auth/refresh")
def refresh(request: Request, response: Response):
    trusted_origin(request)
    value = request.cookies.get("sentinel_refresh", "")
    with db.transaction() as conn:
        # Conditional update ensures a refresh token can be rotated only once.
        query = and_(
            db.sessions.c.refresh_hash == digest(value),
            db.sessions.c.revoked.is_(False),
            db.sessions.c.refresh_expires > time.time(),
        )
        session = conn.execute(select(db.sessions).where(query)).mappings().first()
        if (
            not session
            or not conn.execute(
                db.sessions.update().where(query).values(revoked=True)
            ).rowcount
        ):
            raise HTTPException(401, "Session expired")
        user = find(conn, db.users, session["user_id"])
        if not user["active"]:
            raise HTTPException(401, "Account disabled")
        access, value = new_session(conn, user["id"])
    cookie(response, value)
    return {"access_token": access, "expires_in": 900, "user": public_user(user)}


@router.post("/auth/logout")
def logout(request: Request, response: Response, user=Depends(current_user)):
    with db.transaction() as conn:
        conn.execute(
            db.sessions.update()
            .where(db.sessions.c.user_id == user["id"])
            .values(revoked=True)
        )
    response.delete_cookie("sentinel_refresh", path="/api/v1/auth")
    return {"status": "signed_out"}


@router.get("/auth/me")
def me(user=Depends(current_user)):
    return public_user(user)


@router.get("/public/overview")
def overview():
    with db.transaction() as conn:
        lake_count = conn.execute(
            select(func.count()).select_from(db.lakes)
        ).scalar_one()
        alert_count = len(active_alerts(conn))
    return {
        "lakes": lake_count,
        "alerts": alert_count,
        "mode": "prototype",
        "timezone": "Asia/Kathmandu",
        "limitations": "Automated risk assessment; decision-support system. Not an official disaster prediction.",
        "regions": REGIONS,
    }


def active_alerts(conn):
    timestamp = db.now()
    published = db.rows(
        conn,
        db.alerts,
        and_(
            db.alerts.c.status.in_(["Published", "Updated"]),
            db.alerts.c.effective_at <= timestamp,
            db.alerts.c.expires_at > timestamp,
        ),
    )
    # A pending edit must not withdraw the previously approved public notice.
    revisions = db.rows(
        conn,
        db.alerts,
        and_(
            db.alerts.c.status.in_(["Draft", "Pending approval", "Approved"]),
            db.alerts.c.published_at.is_not(None),
        ),
    )
    for revision in revisions:
        snapshots = conn.execute(
            select(db.versions.c.snapshot)
            .where(db.versions.c.alert_id == revision["id"])
            .order_by(db.versions.c.created_at.desc())
        ).scalars()
        previous = next(
            (s for s in snapshots if s.get("status") in {"Published", "Updated"}), None
        )
        if previous and previous["effective_at"] <= timestamp < previous["expires_at"]:
            published.append(previous)
    return published


@router.get("/public/alerts")
def public_alerts(
    region: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    with db.transaction() as conn:
        records = active_alerts(conn)
    if region:
        records = [r for r in records if r["region"] == region]
    records.sort(key=lambda r: r["published_at"] or "", reverse=True)
    return {
        "items": [
            {k: v for k, v in r.items() if k not in ["created_by", "approved_by"]}
            for r in records[offset : offset + limit]
        ],
        "total": len(records),
    }


@router.get("/public/emergency-resources")
def emergency_resources():
    return {
        "items": [],
        "status": "unavailable",
        "guidance": "No verified shelter inventory is configured. Follow your municipality's official instructions; do not infer safe routes from this map.",
    }


def lake_payload(conn, lake):
    latest = conn.execute(
        select(db.assessments.c.assessment)
        .where(db.assessments.c.lake_id == lake["id"])
        .order_by(db.assessments.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return {**lake, "assessment": latest or assess_lake(lake["properties"])}


@router.get("/public/lakes")
def list_lakes(
    q: str = Query("", max_length=100),
    basin: str = "",
    country: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    sort: Literal["priority", "id"] = "priority",
):
    with db.transaction() as conn:
        result = [lake_payload(conn, lake) for lake in db.rows(conn, db.lakes)]
    result = [
        r
        for r in result
        if q.lower() in json.dumps(r["properties"]).lower()
        and (not basin or r["properties"].get("basin") == basin)
        and (not country or r["properties"].get("country") == country)
    ]
    result.sort(
        key=lambda r: (
            r["assessment"]["overall_monitoring_priority"]["score"]
            if sort == "priority"
            else r["id"]
        ),
        reverse=sort == "priority",
    )
    return {"items": result[offset : offset + limit], "total": len(result)}


@router.get("/public/lakes/{lake_id}")
def lake_detail(lake_id: str):
    with db.transaction() as conn:
        return lake_payload(conn, find(conn, db.lakes, lake_id))


@router.get("/public/lakes/{lake_id}/observations")
def lake_observations(lake_id: str):
    with db.transaction() as conn:
        find(conn, db.lakes, lake_id)
        history = [
            dict(r)
            for r in conn.execute(
                select(db.assessments)
                .where(db.assessments.c.lake_id == lake_id)
                .order_by(db.assessments.c.created_at.desc())
                .limit(30)
            ).mappings()
        ]
        weather = conn.execute(
            select(db.observations.c.payload)
            .where(db.observations.c.location_id == lake_id)
            .order_by(db.observations.c.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
    return {
        "assessments": history,
        "weather": weather,
        "exposure": "Not modelled",
        "lake_change": "Unavailable",
    }


@router.get("/public/map")
def lake_map():
    with db.transaction() as conn:
        result = [lake_payload(conn, r) for r in db.rows(conn, db.lakes)]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": r["id"],
                "geometry": r["geometry"],
                "properties": {
                    **r["properties"],
                    "id": r["id"],
                    "priority": r["assessment"]["overall_monitoring_priority"],
                },
            }
            for r in result
        ],
    }


@router.get("/public/boundaries/{kind}")
def boundaries(kind: Literal["districts", "provinces"]):
    path = boundary_path(kind)
    if not path.exists():
        raise HTTPException(404, "Boundary dataset not installed")
    return FileResponse(
        path,
        media_type="application/geo+json",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Link": f'<{BOUNDARY_LICENSE}>; rel="license"',
            "X-Data-Source": BOUNDARY_SOURCE,
        },
    )


@router.get("/public/weather/{region_id}")
async def weather(region_id: str):
    location = next((r for r in REGIONS if r["id"] == region_id), None)
    if not location:
        raise HTTPException(404, "Region not found")
    return await WeatherProvider().fetch(location)


@router.post("/public/lakes/{lake_id}/explanation")
async def explain(lake_id: str, request: Request, language: Literal["en", "ne"] = "en"):
    throttle(request, "ai", 20, 300)
    with db.transaction() as conn:
        lake = lake_payload(conn, find(conn, db.lakes, lake_id))
    return await AIExplanationProvider().explain(
        {
            "lake": lake["properties"],
            "assessment": lake["assessment"],
            "evidence_ids": [lake["source_id"]],
        },
        language,
    )


@router.get("/reports/verification")
def verification():
    return {
        "mode": "demo"
        if settings.demo_verification and settings.environment == "development"
        else "unavailable",
        "label": "Development mock: no real identity verification. Do not use for emergencies.",
    }


@router.post("/reports", status_code=201)
async def submit_report(
    request: Request,
    region: Annotated[str, Form()],
    category: Annotated[str, Form()],
    description: Annotated[str, Form(min_length=10, max_length=2000)],
    lat: Annotated[float, Form(ge=26, le=31)],
    lng: Annotated[float, Form(ge=80, le=89)],
    observed_at: Annotated[datetime, Form()],
    consent: Annotated[bool, Form()],
    accuracy: Annotated[bool, Form()],
    demo_verified: Annotated[bool, Form()],
    image: Annotated[UploadFile, File()],
    contact: Annotated[str, Form(max_length=200)] = "",
):
    throttle(request, "reports", 5)
    if not settings.demo_verification or settings.environment != "development":
        raise HTTPException(503, "Guest verification provider unavailable")
    if not all([consent, accuracy, demo_verified]):
        raise HTTPException(
            422, "Consent, accuracy declaration and demo verification are required"
        )
    if region not in REGION_IDS or category not in {
        "sudden_river_rise",
        "landslide",
        "blocked_road",
        "damaged_bridge",
        "unusual_water_color",
        "other",
    }:
        raise HTTPException(422, "Unsupported region or incident category")
    if (
        not observed_at.tzinfo
        or observed_at > datetime.now(UTC) + timedelta(minutes=5)
        or observed_at < datetime.now(UTC) - timedelta(days=7)
    ):
        raise HTTPException(
            422, "Observation must be timezone-aware and within the last seven days"
        )
    data = await image.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Image must be at most 5 MB")
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Use JPEG, PNG or WebP")
    try:
        with Image.open(io.BytesIO(data)) as source:
            actual_format = source.format
            source.verify()
        if {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(
            actual_format or ""
        ) != image.content_type:
            raise ValueError("MIME mismatch")
        with Image.open(io.BytesIO(data)) as source:
            clean = ImageOps.exif_transpose(source).convert("RGB")
            clean.thumbnail((1600, 1600))
            output = io.BytesIO()
            clean.save(output, "JPEG", quality=85, exif=b"")
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise HTTPException(415, "Invalid or oversized image") from None
    # Original identity/contact/location are never exposed to public list/map APIs.
    fingerprint = hashlib.sha256(
        data + description.strip().encode() + region.encode()
    ).hexdigest()
    tracking, report_id = secrets.token_urlsafe(32), db.uid()
    storage = settings.storage_dir.resolve()
    storage.mkdir(parents=True, exist_ok=True)
    original_key, derivative_key = f"{db.uid()}.original", f"{db.uid()}.jpg"
    try:
        with db.transaction() as conn:
            if conn.execute(
                select(db.reports.c.id).where(db.reports.c.content_hash == fingerprint)
            ).first():
                raise HTTPException(
                    409, "Duplicate report; use your original tracking link"
                )
            (storage / original_key).write_bytes(data)
            (storage / derivative_key).write_bytes(output.getvalue())
            conn.execute(
                db.reports.insert().values(
                    id=report_id,
                    tracking_hash=digest(tracking),
                    region=region,
                    category=category,
                    description=description.strip(),
                    lat=lat,
                    lng=lng,
                    observed_at=observed_at.astimezone(UTC).isoformat(),
                    contact=contact,
                    status="Submitted",
                    media_key=original_key,
                    derivative_key=derivative_key,
                    content_hash=fingerprint,
                )
            )
            db.record(
                conn,
                None,
                "report.submitted",
                report_id,
                {
                    "checks": [
                        "schema",
                        "mime",
                        "size",
                        "recency",
                        "bounds",
                        "duplicate",
                    ],
                    "verification": "development_mock",
                },
            )
    except Exception:
        (storage / original_key).unlink(missing_ok=True)
        (storage / derivative_key).unlink(missing_ok=True)
        raise
    return {
        "id": report_id,
        "tracking_id": tracking,
        "status": "Submitted",
        "verification_mode": "demo",
        "message": "Unverified observation received for private human review.",
    }


@router.get("/reports/{tracking_id}")
def track_report(tracking_id: str, request: Request):
    throttle(request, "tracking", 60, 300)
    with db.transaction() as conn:
        r = (
            conn.execute(
                select(db.reports).where(
                    db.reports.c.tracking_hash == digest(tracking_id)
                )
            )
            .mappings()
            .first()
        )
    if not r:
        raise HTTPException(404, "Tracking code not found")
    return {key: r[key] for key in ("id", "status", "created_at", "updated_at")}


@router.get("/staff/reports/{report_id}/media")
def evidence(report_id: str, user=Depends(current_user)):
    with db.transaction() as conn:
        report = find(conn, db.reports, report_id)
        jurisdiction(user, report["region"])
        if user["role"] not in {"admin", "government"}:
            raise HTTPException(403, "Staff access required")
        db.record(conn, user["id"], "evidence.viewed", report_id)
    return FileResponse(
        settings.storage_dir / report["derivative_key"],
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


def scoped(conn, table, user):
    return db.rows(
        conn,
        table,
        table.c.region.in_(user["jurisdictions"])
        if user["role"] == "government"
        else None,
    )


def report_list(user, status, offset, limit):
    with db.transaction() as conn:
        records = scoped(conn, db.reports, user)
    if user["role"] == "government":
        records = [r for r in records if r["status"] != "Submitted"]
    if status:
        records = [r for r in records if r["status"] == status]
    records.sort(key=lambda r: r["created_at"], reverse=True)
    private = {
        "contact",
        "tracking_hash",
        "content_hash",
        "media_key",
        "derivative_key",
    }
    return {
        "items": [
            {k: v for k, v in r.items() if k not in private}
            for r in records[offset : offset + limit]
        ],
        "total": len(records),
    }


@router.get("/admin/reports")
def admin_reports(
    status: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(admin),
):
    return report_list(user, status, offset, limit)


@router.get("/government/reports")
def gov_reports(
    status: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(official),
):
    return report_list(user, status, offset, limit)


@router.post("/admin/reports/{report_id}/review")
def moderate(report_id: str, payload: Review, user=Depends(admin)):
    if payload.action not in {"escalate", "reject"}:
        raise HTTPException(
            422, "Administrators can escalate or reject; officials confirm incidents"
        )
    with db.transaction() as conn:
        r = find(conn, db.reports, report_id)
        if r["status"] != "Submitted":
            raise HTTPException(409, "Report already moderated")
        status = "Escalated" if payload.action == "escalate" else "Rejected"
        changed = conn.execute(
            db.reports.update()
            .where(
                and_(db.reports.c.id == report_id, db.reports.c.status == "Submitted")
            )
            .values(status=status, updated_at=db.now())
        )
        if not changed.rowcount:
            raise HTTPException(409, "Report changed; reload")
        db.record(
            conn,
            user["id"],
            "report." + payload.action,
            report_id,
            {"reason": payload.reason},
        )
    return {"status": status}


@router.post("/government/reports/{report_id}/review")
def verify(report_id: str, payload: Review, user=Depends(official)):
    if payload.action == "escalate":
        raise HTTPException(422, "Use confirm, reject or request_verification")
    with db.transaction() as conn:
        r = find(conn, db.reports, report_id)
        jurisdiction(user, r["region"])
        if r["status"] not in {"Escalated", "Field verification requested"}:
            raise HTTPException(409, "Report is not awaiting government review")
        status = {
            "confirm": "Verified",
            "reject": "Rejected",
            "request_verification": "Field verification requested",
        }[payload.action]
        changed = conn.execute(
            db.reports.update()
            .where(
                and_(db.reports.c.id == report_id, db.reports.c.status == r["status"])
            )
            .values(status=status, updated_at=db.now())
        )
        if not changed.rowcount:
            raise HTTPException(409, "Report changed; reload")
        incident_id = None
        if payload.action == "confirm":
            incident_id = db.uid()
            conn.execute(
                db.incidents.insert().values(
                    id=incident_id,
                    report_id=report_id,
                    region=r["region"],
                    severity=payload.severity,
                    status="Confirmed",
                    evidence_summary=payload.reason,
                    actions=[],
                )
            )
        db.record(
            conn,
            user["id"],
            "report." + payload.action,
            report_id,
            {"reason": payload.reason, "incident_id": incident_id},
        )
    return {"status": status, "incident_id": incident_id}


@router.get("/government/incidents")
def incident_list(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(official),
):
    with db.transaction() as conn:
        records = scoped(conn, db.incidents, user)
    return {"items": records[offset : offset + limit], "total": len(records)}


@router.patch("/government/incidents/{incident_id}")
def update_incident(incident_id: str, payload: IncidentUpdate, user=Depends(official)):
    with db.transaction() as conn:
        item = find(conn, db.incidents, incident_id)
        jurisdiction(user, item["region"])
        if item["status"] == "Resolved":
            raise HTTPException(409, "Incident is already resolved")
        if payload.status == "Resolved" and db.rows(
            conn,
            db.alerts,
            and_(
                db.alerts.c.incident_id == incident_id,
                db.alerts.c.status.in_(["Published", "Updated"]),
            ),
        ):
            raise HTTPException(
                409, "Resolve or cancel published alerts before closing incident"
            )
        conn.execute(
            db.incidents.update()
            .where(db.incidents.c.id == incident_id)
            .values(status=payload.status, actions=payload.actions, updated_at=db.now())
        )
        db.record(
            conn, user["id"], "incident.updated", incident_id, payload.model_dump()
        )
    return {"status": payload.status}


@router.get("/government/incidents/{incident_id}/export")
def export_incident(incident_id: str, user=Depends(official)):
    with db.transaction() as conn:
        item = find(conn, db.incidents, incident_id)
        jurisdiction(user, item["region"])
        history = db.rows(
            conn, db.audit, db.audit.c.entity_id.in_([incident_id, item["report_id"]])
        )
        notices = db.rows(conn, db.alerts, db.alerts.c.incident_id == incident_id)
        db.record(conn, user["id"], "incident.exported", incident_id)
    return {
        "incident": item,
        "alerts": notices,
        "history": history,
        "exported_at": db.now(),
        "is_demo": settings.environment == "development",
    }


@router.post("/government/incidents/{incident_id}/ai-draft")
async def ai_draft(incident_id: str, request: Request, user=Depends(official)):
    throttle(request, "ai", 20, 300)
    with db.transaction() as conn:
        item = find(conn, db.incidents, incident_id)
        jurisdiction(user, item["region"])
    return await AIExplanationProvider().explain(
        {"incident": item, "evidence_ids": [item["report_id"]]}
    )


@router.get("/government/alerts")
def alert_list(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(official),
):
    with db.transaction() as conn:
        records = scoped(conn, db.alerts, user)
    records.sort(key=lambda a: a["updated_at"], reverse=True)
    return {"items": records[offset : offset + limit], "total": len(records)}


def save_version(conn, item):
    conn.execute(
        db.versions.insert().values(id=db.uid(), alert_id=item["id"], snapshot=item)
    )


@router.post("/government/alerts", status_code=201)
def create_alert(payload: AlertDraft, user=Depends(official)):
    with db.transaction() as conn:
        incident = find(conn, db.incidents, payload.incident_id)
        jurisdiction(user, incident["region"])
        if incident["status"] == "Resolved":
            raise HTTPException(409, "Incident is resolved")
        item = {
            **payload.model_dump(mode="json"),
            "effective_at": payload.effective_at.astimezone(UTC).isoformat(),
            "expires_at": payload.expires_at.astimezone(UTC).isoformat(),
            "id": db.uid(),
            "region": incident["region"],
            "status": "Draft",
            "created_by": user["id"],
            "is_demo": settings.environment == "development",
        }
        conn.execute(db.alerts.insert().values(**item))
        save_version(conn, item)
        db.record(conn, user["id"], "alert.drafted", item["id"])
    return item


@router.put("/government/alerts/{alert_id}")
def edit_alert(alert_id: str, payload: AlertDraft, user=Depends(official)):
    with db.transaction() as conn:
        item = find(conn, db.alerts, alert_id)
        jurisdiction(user, item["region"])
        if payload.incident_id != item["incident_id"] or item["status"] not in {
            "Draft",
            "Pending approval",
            "Approved",
            "Published",
            "Updated",
        }:
            raise HTTPException(409, "Alert cannot be edited in this state")
        # Every substantive edit requires a fresh approval, including published updates.
        values = {
            **payload.model_dump(mode="json"),
            "effective_at": payload.effective_at.astimezone(UTC).isoformat(),
            "expires_at": payload.expires_at.astimezone(UTC).isoformat(),
            "status": "Draft",
            "approved_by": None,
            "updated_at": db.now(),
        }
        conn.execute(
            db.alerts.update().where(db.alerts.c.id == alert_id).values(**values)
        )
        save_version(conn, {**item, **values})
        db.record(conn, user["id"], "alert.edited_requires_approval", alert_id)
    return {"status": "Draft"}


@router.post("/government/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: str, payload: AlertAction, user=Depends(official)):
    with db.transaction() as conn:
        item = find(conn, db.alerts, alert_id)
        jurisdiction(user, item["region"])
        db.record(
            conn, user["id"], "alert.acknowledged", alert_id, {"reason": payload.reason}
        )
    return {"status": "acknowledged"}


@router.post("/government/alerts/{alert_id}/{action}")
def transition_alert(
    alert_id: str,
    action: Literal["submit", "approve", "publish", "cancel", "resolve"],
    payload: AlertAction,
    user=Depends(official),
):
    transitions = {
        "submit": ({"Draft"}, "Pending approval"),
        "approve": ({"Pending approval"}, "Approved"),
        "publish": ({"Approved"}, "Published"),
        "cancel": (
            {"Draft", "Pending approval", "Approved", "Published", "Updated"},
            "Cancelled",
        ),
        "resolve": ({"Published", "Updated"}, "Resolved"),
    }
    with db.transaction() as conn:
        item = find(conn, db.alerts, alert_id)
        jurisdiction(user, item["region"])
        allowed, status = transitions[action]
        if item["status"] not in allowed:
            raise HTTPException(409, "Invalid alert lifecycle transition")
        if action in {"approve", "publish"} and item["expires_at"] <= db.now():
            raise HTTPException(409, "Alert has expired")
        values = {
            "status": "Updated"
            if action == "publish" and item["published_at"]
            else status,
            "reason": payload.reason,
            "updated_at": db.now(),
        }
        if action == "approve":
            values["approved_by"] = user["id"]
        if action == "publish":
            if not item["approved_by"]:
                raise HTTPException(409, "Approval required")
            values["published_at"] = db.now()
        changed = conn.execute(
            db.alerts.update()
            .where(
                and_(db.alerts.c.id == alert_id, db.alerts.c.status == item["status"])
            )
            .values(**values)
        )
        if not changed.rowcount:
            raise HTTPException(409, "Alert changed; reload")
        if action == "publish":
            for channel in ("in_app", "email", "sms"):
                delivery = NotificationProvider().deliver(channel, item)
                conn.execute(
                    db.deliveries.insert().values(
                        id=db.uid(), alert_id=alert_id, channel=channel, **delivery
                    )
                )
        save_version(conn, {**item, **values})
        db.record(
            conn, user["id"], "alert." + action, alert_id, {"reason": payload.reason}
        )
    return {"status": values["status"]}


@router.get("/government/alerts/{alert_id}/history")
def alert_history(alert_id: str, user=Depends(official)):
    with db.transaction() as conn:
        item = find(conn, db.alerts, alert_id)
        jurisdiction(user, item["region"])
        return {"items": db.rows(conn, db.versions, db.versions.c.alert_id == alert_id)}


@router.get("/government/dashboard")
def government_dashboard(user=Depends(official)):
    with db.transaction() as conn:
        return {
            "jurisdictions": user["jurisdictions"],
            "reports": len(scoped(conn, db.reports, user)),
            "incidents": len(scoped(conn, db.incidents, user)),
            "alerts": len(scoped(conn, db.alerts, user)),
            "exposure_status": "Not modelled",
        }


@router.get("/admin/dashboard")
def admin_dashboard(user=Depends(admin)):
    with db.transaction() as conn:
        return {
            "database": "ok",
            "reports": conn.execute(
                select(func.count()).select_from(db.reports)
            ).scalar_one(),
            "lakes": conn.execute(
                select(func.count()).select_from(db.lakes)
            ).scalar_one(),
            "risk_engine": ENGINE_VERSION,
            "evidence_storage": str(settings.storage_dir),
            "verification": "demo" if settings.demo_verification else "unavailable",
        }


@router.get("/admin/users")
def list_users(user=Depends(admin)):
    with db.transaction() as conn:
        return {"items": [public_user(u) for u in db.rows(conn, db.users)]}


@router.post("/admin/users", status_code=201)
def create_user(payload: UserCreate, user=Depends(admin)):
    if len(payload.password) < 12 or not set(payload.jurisdictions) <= REGION_IDS:
        raise HTTPException(
            422, "Use a 12+ character password and supported jurisdictions"
        )
    with db.transaction() as conn:
        if conn.execute(
            select(db.users.c.id).where(db.users.c.email == payload.email.lower())
        ).first():
            raise HTTPException(409, "Account already exists")
        identifier = db.uid()
        conn.execute(
            db.users.insert().values(
                id=identifier,
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                role=payload.role,
                jurisdictions=payload.jurisdictions,
                active=True,
            )
        )
        db.record(conn, user["id"], "user.created", identifier, {"role": payload.role})
    return {"id": identifier}


@router.patch("/admin/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate, user=Depends(admin)):
    if user_id == user["id"] and not payload.active:
        raise HTTPException(409, "Cannot disable your own account")
    if not set(payload.jurisdictions) <= REGION_IDS:
        raise HTTPException(422, "Unsupported jurisdiction")
    with db.transaction() as conn:
        find(conn, db.users, user_id)
        conn.execute(
            db.users.update()
            .where(db.users.c.id == user_id)
            .values(**payload.model_dump())
        )
        conn.execute(
            db.sessions.update()
            .where(db.sessions.c.user_id == user_id)
            .values(revoked=True)
        )
        db.record(conn, user["id"], "user.updated", user_id, payload.model_dump())
    return {"status": "updated"}


@router.get("/admin/{resource}")
def admin_resource(
    resource: Literal[
        "data-sources",
        "sync-runs",
        "audit-logs",
        "deliveries",
        "risk-settings",
        "templates",
        "data-quality",
    ],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user=Depends(admin),
):
    table = {
        "data-sources": db.sources,
        "sync-runs": db.sync_runs,
        "audit-logs": db.audit,
        "deliveries": db.deliveries,
        "risk-settings": db.config,
        "templates": db.config,
    }.get(resource)
    if resource == "data-quality":
        path = ROOT / "backend/data/processed/data-quality.json"
        return (
            json.loads(path.read_text(encoding="utf-8"))
            if path.exists()
            else {"items": [], "status": "Run inspect_datasets.py"}
        )
    assert table is not None
    with db.transaction() as conn:
        query: Select = select(table)
        if "created_at" in table.c:
            query = query.order_by(table.c.created_at.desc())
        records = [
            dict(r) for r in conn.execute(query.offset(offset).limit(limit)).mappings()
        ]
    return {"items": records}


@router.put("/admin/risk-settings")
def risk_settings(payload: SettingUpdate, user=Depends(admin)):
    with db.transaction() as conn:
        conn.execute(db.config.delete().where(db.config.c.id == "thresholds"))
        conn.execute(
            db.config.insert().values(id="thresholds", value=payload.model_dump())
        )
        db.record(
            conn,
            user["id"],
            "risk.thresholds.updated",
            ENGINE_VERSION,
            payload.model_dump(),
        )
    return {
        "status": "saved",
        "note": "Applied on next risk recalculation; historical assessments retain their thresholds",
    }


@router.put("/admin/templates")
def template_settings(payload: TemplateUpdate, user=Depends(admin)):
    with db.transaction() as conn:
        conn.execute(db.config.delete().where(db.config.c.id == "alert-template"))
        conn.execute(
            db.config.insert().values(id="alert-template", value=payload.model_dump())
        )
        db.record(conn, user["id"], "alert.template.updated", "alert-template")
    return {"status": "saved"}


@router.get("/government/alert-template")
def alert_template(user=Depends(official)):
    with db.transaction() as conn:
        value = conn.execute(
            select(db.config.c.value).where(db.config.c.id == "alert-template")
        ).scalar_one_or_none()
    return value or {"safety_instructions": " ".join(SAFETY)}


@router.post("/admin/data-sources/{provider_id}/{action}")
async def source_action(
    provider_id: str,
    action: Literal["sync", "enable", "disable"],
    payload: AlertAction,
    user=Depends(admin),
):
    with db.transaction() as conn:
        source = find(conn, db.sources, provider_id)
        if action != "sync":
            conn.execute(
                db.sources.update()
                .where(db.sources.c.id == provider_id)
                .values(enabled=action == "enable")
            )
        db.record(
            conn,
            user["id"],
            "provider." + action,
            provider_id,
            {"reason": payload.reason},
        )
    if action == "sync":
        if not source["enabled"]:
            raise HTTPException(409, "Provider disabled")
        if provider_id != "weather":
            raise HTTPException(409, "No authorized adapter configured")
        from .jobs import sync_weather

        return await sync_weather()
    return {"status": action + "d"}


def initialize():
    db.migrate()
    with db.transaction() as conn:
        for key, state in provider_states().items():
            if not conn.execute(
                select(db.sources.c.id).where(db.sources.c.id == key)
            ).first():
                conn.execute(
                    db.sources.insert().values(id=key, state=state, enabled=True)
                )
