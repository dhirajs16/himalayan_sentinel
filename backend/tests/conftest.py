import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app import db
from app.config import settings
from app.main import app
from app.security import hash_password


@pytest.fixture
def system(tmp_path, monkeypatch):
    base_engine = None
    schema = None
    if os.environ.get("TEST_POSTGRES") == "1":
        if not settings.database_url.startswith("postgresql"):
            pytest.fail("TEST_POSTGRES requires a PostgreSQL DATABASE_URL")
        # All test tables, raw SQL and spatial indexes stay in a new private schema.
        # Public application records and uploaded evidence are never reset.
        schema = "sentinel_test_" + uuid4().hex
        base_engine = db.make_engine(settings.database_url)
        with base_engine.begin() as conn:
            conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        engine = create_engine(
            settings.database_url,
            connect_args={"options": f"-csearch_path={schema},public"},
            pool_pre_ping=True,
            execution_options={"schema_translate_map": {None: schema}},
        )
    else:
        engine = db.make_engine("sqlite:///" + (tmp_path / "test.db").as_posix())
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(settings, "storage_dir", tmp_path / "private")
    monkeypatch.setattr(settings, "weather_live", False)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "demo_verification", True)
    try:
        with TestClient(app) as client:
            with db.transaction() as conn:
                for identifier, role, jurisdictions in [
                    ("admin", "admin", []),
                    ("official", "government", ["rasuwa"]),
                    ("other", "government", ["dolakha"]),
                ]:
                    conn.execute(
                        db.users.insert().values(
                            id=identifier,
                            email=identifier + "@example.test",
                            role=role,
                            jurisdictions=jurisdictions,
                            active=True,
                            password_hash=hash_password("TestPassword123!"),
                        )
                    )
            yield client
    finally:
        engine.dispose()
        if base_engine is not None and schema is not None:
            with base_engine.begin() as conn:
                # Only the internally generated test schema is removed.
                conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
            base_engine.dispose()


@pytest.fixture
def auth(system):
    def get(identifier):
        response = system.post(
            "/api/v1/auth/login",
            json={
                "email": identifier + "@example.test",
                "password": "TestPassword123!",
            },
        )
        assert response.status_code == 200, response.text
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    return get
