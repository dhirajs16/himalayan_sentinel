"""Portable transactional store. PostGIS spatial columns are added by migration 2."""

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    event,
    text,
)

from .config import settings


def now():
    return datetime.now(UTC).isoformat()


def uid():
    return str(uuid4())


metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("id", String, primary_key=True),
    Column("email", String, unique=True, nullable=False),
    Column("password_hash", Text, nullable=False),
    Column("role", String, nullable=False),
    Column("jurisdictions", JSON, nullable=False),
    Column("active", Boolean, default=True),
    Column("created_at", String, default=now),
)
sessions = Table(
    "sessions",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False, index=True),
    Column("access_hash", String, unique=True),
    Column("refresh_hash", String, unique=True),
    Column("access_expires", Float),
    Column("refresh_expires", Float),
    Column("revoked", Boolean, default=False),
)
reports = Table(
    "citizen_reports",
    metadata,
    Column("id", String, primary_key=True),
    Column("tracking_hash", String, unique=True),
    Column("region", String, index=True),
    Column("category", String),
    Column("description", Text),
    Column("lat", Float),
    Column("lng", Float),
    Column("observed_at", String),
    Column("contact", String),
    Column("status", String, index=True),
    Column("media_key", String),
    Column("derivative_key", String),
    Column("content_hash", String, unique=True),
    Column("created_at", String, default=now),
    Column("updated_at", String, default=now),
)
incidents = Table(
    "incidents",
    metadata,
    Column("id", String, primary_key=True),
    Column("report_id", String, unique=True),
    Column("region", String, index=True),
    Column("severity", String),
    Column("status", String),
    Column("evidence_summary", Text),
    Column("actions", JSON),
    Column("created_at", String, default=now),
    Column("updated_at", String, default=now),
)
alerts = Table(
    "alerts",
    metadata,
    Column("id", String, primary_key=True),
    Column("incident_id", String),
    Column("region", String, index=True),
    Column("title", String),
    Column("disaster_type", String),
    Column("severity", String),
    Column("description", Text),
    Column("evidence_summary", Text),
    Column("safety_instructions", Text),
    Column("resources", JSON),
    Column("effective_at", String),
    Column("expires_at", String),
    Column("status", String, index=True),
    Column("created_by", String),
    Column("approved_by", String),
    Column("published_at", String),
    Column("reason", Text),
    Column("is_demo", Boolean, default=True),
    Column("created_at", String, default=now),
    Column("updated_at", String, default=now),
)
audit = Table(
    "audit_logs",
    metadata,
    Column("id", String, primary_key=True),
    Column("actor_id", String),
    Column("action", String),
    Column("entity_id", String, index=True),
    Column("details", JSON),
    Column("created_at", String, default=now),
)
versions = Table(
    "alert_versions",
    metadata,
    Column("id", String, primary_key=True),
    Column("alert_id", String, index=True),
    Column("snapshot", JSON),
    Column("created_at", String, default=now),
)
deliveries = Table(
    "alert_deliveries",
    metadata,
    Column("id", String, primary_key=True),
    Column("alert_id", String),
    Column("channel", String),
    Column("status", String),
    Column("detail", String),
    Column("created_at", String, default=now),
)
lakes = Table(
    "glacial_lakes",
    metadata,
    Column("id", String, primary_key=True),
    Column("source_id", String, unique=True),
    Column("properties", JSON),
    Column("geometry", JSON),
    Column("lat", Float),
    Column("lng", Float),
    Column("created_at", String, default=now),
)
assessments = Table(
    "risk_assessments",
    metadata,
    Column("id", String, primary_key=True),
    Column("lake_id", String, index=True),
    Column("assessment", JSON),
    Column("created_at", String, default=now),
)
sources = Table(
    "data_sources",
    metadata,
    Column("id", String, primary_key=True),
    Column("state", JSON),
    Column("enabled", Boolean, default=True),
)
sync_runs = Table(
    "data_sync_runs",
    metadata,
    Column("id", String, primary_key=True),
    Column("provider", String),
    Column("status", String),
    Column("details", JSON),
    Column("created_at", String, default=now),
)
observations = Table(
    "weather_observations",
    metadata,
    Column("id", String, primary_key=True),
    Column("location_id", String, index=True),
    Column("payload", JSON),
    Column("created_at", String, default=now),
)
config = Table(
    "system_settings",
    metadata,
    Column("id", String, primary_key=True),
    Column("value", JSON),
)
limits = Table(
    "rate_limits",
    metadata,
    Column("id", String, primary_key=True),
    Column("window", Integer),
    Column("count", Integer),
)


def make_engine(url):
    if url.startswith("sqlite:"):
        Path("var").mkdir(exist_ok=True)
    result = create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": 30}
        if url.startswith("sqlite:")
        else {},
        pool_pre_ping=True,
    )
    if url.startswith("sqlite:"):

        @event.listens_for(result, "connect")
        def pragmas(connection, _):
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")

    return result


engine = make_engine(settings.database_url)


def migrate():
    """Versioned, idempotent clean-database migration; never drops user records."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)"
            )
        )
        metadata.create_all(conn)
        conn.execute(
            text(
                "INSERT INTO schema_migrations (version) VALUES (1) ON CONFLICT DO NOTHING"
            )
        )
        if engine.dialect.name == "postgresql":
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.execute(
                text(
                    "ALTER TABLE glacial_lakes ADD COLUMN IF NOT EXISTS geom geometry(Geometry,4326)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS lakes_geom_gist ON glacial_lakes USING GIST (geom)"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS administrative_regions (id TEXT PRIMARY KEY, properties JSONB, geom geometry(Geometry,4326))"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS regions_geom_gist ON administrative_regions USING GIST (geom)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO schema_migrations (version) VALUES (2) ON CONFLICT DO NOTHING"
                )
            )


@contextmanager
def transaction():
    with engine.begin() as conn:
        yield conn


def rows(conn, table, condition=None):
    query = table.select()
    if condition is not None:
        query = query.where(condition)
    return [dict(row) for row in conn.execute(query).mappings()]


def record(conn, actor, action, entity_id, details=None):
    conn.execute(
        audit.insert().values(
            id=uid(),
            actor_id=actor,
            action=action,
            entity_id=entity_id,
            details=details or {},
        )
    )


if __name__ == "__main__":
    migrate()
    print("Database migrations complete")
