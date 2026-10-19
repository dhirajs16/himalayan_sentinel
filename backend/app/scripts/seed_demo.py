"""Run from backend: python -m app.scripts.seed_demo (explicit env credentials)."""

import json
from pathlib import Path

from sqlalchemy import select

from app import db
from app.config import settings
from app.security import hash_password


def seed():
    if settings.environment != "development":
        raise RuntimeError("Demo seeding is development-only")
    credentials = [
        (settings.admin_email, settings.admin_password, "admin"),
        (settings.government_email, settings.government_password, "government"),
    ]
    if any(not email or len(password) < 12 for email, password, _ in credentials):
        raise RuntimeError(
            "Set ADMIN_EMAIL/PASSWORD and GOVERNMENT_EMAIL/PASSWORD from .env.example (12+ characters)"
        )
    db.migrate()
    with db.transaction() as conn:
        for email, password, role in credentials:
            if not conn.execute(
                select(db.users.c.id).where(db.users.c.email == email.lower())
            ).first():
                conn.execute(
                    db.users.insert().values(
                        id=db.uid(),
                        email=email.lower(),
                        password_hash=hash_password(password),
                        role=role,
                        jurisdictions=[
                            r["id"]
                            for r in json.loads(
                                (
                                    Path(__file__).parents[1] / "data/regions.json"
                                ).read_text(encoding="utf-8")
                            )
                        ],
                        active=True,
                    )
                )
    print("Demo accounts ready; existing accounts preserved")


if __name__ == "__main__":
    seed()
