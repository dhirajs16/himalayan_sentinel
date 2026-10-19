"""Convert local PDGL polygons; retain every transboundary source record."""

import json
import sys
from pathlib import Path

import shapefile
from pyproj import CRS, Transformer
from shapely import transform
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
ATTRIBUTION = "ICIMOD. (2020). Potentially dangerous glacial lakes in the Koshi, Gandaki, and Karnali river basins of Nepal, the Tibet Autonomous Region of China, and India [Data set]. ICIMOD. https://doi.org/10.26066/RDS.1971950"


def preprocess():
    matches = list((ROOT / "data").rglob("PDGLs.shp"))
    if len(matches) != 1:
        raise RuntimeError("Expected one local PDGLs.shp; install licensed data first")
    path = matches[0]
    reader = shapefile.Reader(str(path))
    names = [field[0] for field in reader.fields[1:]]
    required = {"GL_ID", "Rank", "Country", "Basin"}
    if not required <= set(names):
        raise ValueError(f"Missing source fields: {required - set(names)}")
    transformer = Transformer.from_crs(
        CRS.from_wkt(path.with_suffix(".prj").read_text()), 4326, always_xy=True
    )
    features, source_ids = [], set()
    for sr in reader.iterShapeRecords():
        raw = dict(zip(names, sr.record))
        source_id = str(raw["GL_ID"])
        if source_id in source_ids:
            raise ValueError("Duplicate GL_ID: " + source_id)
        source_ids.add(source_id)
        geom = transform(
            shape(sr.shape.__geo_interface__), transformer.transform, interleaved=False
        )
        if not geom.is_valid or geom.is_empty:
            raise ValueError(
                "Invalid source geometry; do not silently repair: " + source_id
            )
        props = {key.lower(): value for key, value in raw.items()}
        props.update(
            source_id=source_id,
            name=source_id,
            attribution=ATTRIBUTION,
            source_date="2020-09-10",
            inventory_imagery_year=2015,
            mode="static",
            raw_properties=raw,
        )
        features.append(
            {
                "type": "Feature",
                "id": source_id,
                "properties": props,
                "geometry": mapping(geom),
            }
        )
    collection = {
        "type": "FeatureCollection",
        "features": features,
        "attribution": ATTRIBUTION,
    }
    output = ROOT / "backend/data/processed"
    output.mkdir(parents=True, exist_ok=True)
    (output / "pdgl.geojson").write_text(
        json.dumps(collection, ensure_ascii=False), encoding="utf-8"
    )
    # Local fixture retains source attribution; do not commit until redistribution licence is verified.
    (output / "pdgl-sample.geojson").write_text(
        json.dumps({**collection, "features": features[:3]}), encoding="utf-8"
    )
    print(f"Prepared {len(features)} original polygons; all countries retained")
    return collection


if __name__ == "__main__":
    preprocess()
