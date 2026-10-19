"""Create a dedicated native database and save its URL without exposing credentials."""

import argparse
import io
from pathlib import Path

import psycopg
from dotenv import dotenv_values, set_key
from psycopg import sql
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[3]


def configure(from_commented=False):
    env_path = ROOT / ".env"
    values = {}
    if from_commented:
        # Explicit opt-in for credentials the owner has provided as commented settings.
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
        values.update(
            dotenv_values(
                stream=io.StringIO(
                    "\n".join(
                        line.lstrip()[1:].strip()
                        for line in lines
                        if line.lstrip().startswith("#") and "=" in line
                    )
                )
            )
        )
    values.update({k: v for k, v in dotenv_values(env_path).items() if v})
    user = values.get("DB_USERNAME") or values.get("DB_USER") or values.get("PGUSER")
    password = values.get("DB_PASSWORD") or values.get("PGPASSWORD")
    if not user or not password:
        raise SystemExit(
            "Set DB_USERNAME and DB_PASSWORD privately in .env; use --from-commented only for explicitly supplied commented values."
        )
    host = values.get("DB_HOST") or values.get("PGHOST") or "localhost"
    port = int(values.get("DB_PORT") or values.get("PGPORT") or 5432)
    database = "himalayan_sentinel"
    connection = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "connect_timeout": 5,
    }
    with psycopg.connect(**connection, dbname="postgres", autocommit=True) as conn:
        if not conn.execute(
            "SELECT 1 FROM pg_available_extensions WHERE name = 'postgis'"
        ).fetchone():
            raise SystemExit(
                "Install the PostgreSQL-compatible PostGIS package before creating the spatial database."
            )
        if not conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
        ).fetchone():
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
            print("Created dedicated Himalayan Sentinel database")
    with psycopg.connect(**connection, dbname=database) as conn:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).fetchall()
        }
        if (
            tables - {"spatial_ref_sys"}
            and not {"schema_migrations", "glacial_lakes", "citizen_reports"} <= tables
        ):
            raise SystemExit(
                "The named database contains unrelated tables; setup stopped without changing them."
            )
        conn.execute("CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public")
        version = conn.execute("SELECT postgis_version()").fetchone()[0]
    url = URL.create(
        "postgresql+psycopg",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    set_key(
        str(env_path),
        "DATABASE_URL",
        url.render_as_string(hide_password=False),
        quote_mode="always",
    )
    print(
        f"PostGIS {version} enabled; private DATABASE_URL configured for {host}:{port}/{database}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-commented", action="store_true")
    try:
        configure(parser.parse_args().from_commented)
    except psycopg.Error as exc:
        raise SystemExit(
            exc.diag.message_primary
            or "PostgreSQL connection failed; check the private .env credentials"
        ) from None
