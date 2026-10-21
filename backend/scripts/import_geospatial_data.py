import json
import sys
from pathlib import Path

from shapely.geometry import shape
from sqlalchemy import select, text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from preprocess_datasets import preprocess

from app import db
from app.boundaries import boundary_path
from app.risk_engine import assess_lake


def import_data():
    collection = preprocess()
    db.migrate()
    with db.transaction() as conn:
        for feature in collection["features"]:
            identifier = str(feature["id"])
            geometry = shape(feature["geometry"])
            center = geometry.representative_point()
            values = {
                "source_id": identifier,
                "properties": feature["properties"],
                "geometry": feature["geometry"],
                "lat": center.y,
                "lng": center.x,
            }
            exists = conn.execute(
                select(db.lakes.c.id).where(db.lakes.c.id == identifier)
            ).first()
            if exists:
                conn.execute(
                    db.lakes.update()
                    .where(db.lakes.c.id == identifier)
                    .values(**values)
                )
            else:
                conn.execute(db.lakes.insert().values(id=identifier, **values))
                conn.execute(
                    db.assessments.insert().values(
                        id=db.uid(),
                        lake_id=identifier,
                        assessment=assess_lake(values["properties"]),
                    )
                )
            if db.engine.dialect.name == "postgresql":
                conn.execute(
                    text(
                        "UPDATE glacial_lakes SET geom = ST_SetSRID(ST_GeomFromGeoJSON(:geom),4326) WHERE id = :id"
                    ),
                    {"geom": json.dumps(feature["geometry"]), "id": identifier},
                )
        if db.engine.dialect.name == "postgresql":
            for kind in ("districts", "provinces"):
                source = boundary_path(kind)
                if not source.exists():
                    continue
                for index, feature in enumerate(
                    json.loads(source.read_text(encoding="utf-8"))["features"]
                ):
                    conn.execute(
                        text(
                            "INSERT INTO administrative_regions (id, properties, geom) VALUES (:id, CAST(:props AS jsonb), ST_SetSRID(ST_GeomFromGeoJSON(:geom),4326)) ON CONFLICT (id) DO UPDATE SET properties=EXCLUDED.properties, geom=EXCLUDED.geom"
                        ),
                        {
                            "id": f"{kind}-{index}",
                            "props": json.dumps(feature["properties"]),
                            "geom": json.dumps(feature["geometry"]),
                        },
                    )
        db.record(
            conn,
            None,
            "dataset.imported",
            "icimod-pdgl",
            {"records": len(collection["features"]), "raw_modified": False},
        )
    print("Idempotent spatial import complete")


if __name__ == "__main__":
    import_data()
