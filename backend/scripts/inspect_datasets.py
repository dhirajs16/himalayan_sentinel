"""Read-only recursive inventory. Run from backend; writes only processed outputs."""

import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import rasterio
import shapefile
from pypdf import PdfReader
from pyproj import CRS
from shapely.geometry import shape
from shapely.validation import explain_validity

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def geometry_quality(features):
    invalid, empty = [], 0
    for index, feature in enumerate(features):
        geom = shape(feature["geometry"])
        empty += int(geom.is_empty)
        if not geom.is_valid:
            invalid.append({"index": index, "reason": explain_validity(geom)})
    return {"invalid_geometries": invalid, "empty_geometries": empty}


def tabular(records):
    fields = sorted({key for r in records for key in r})
    return {
        "records": len(records),
        "schema": {
            key: sorted({type(r.get(key)).__name__ for r in records}) for key in fields
        },
        "missing": {
            key: sum(r.get(key) in [None, "", "NA", "N/A"] for r in records)
            for key in fields
        },
        "duplicate_rows": len(records)
        - len({json.dumps(r, sort_keys=True, default=str) for r in records}),
    }


def inspect(path):
    data = path.read_bytes()
    result = {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "format": path.suffix.lower(),
        "classification": "static",
        "licence": "See accompanying metadata and agreement; verification required before redistribution",
    }
    if path.suffix.lower() == ".shp":
        reader = shapefile.Reader(str(path))
        fields = [f[0] for f in reader.fields[1:]]
        records = [dict(zip(fields, r)) for r in reader.records()]
        features = [{"geometry": s.__geo_interface__} for s in reader.shapes()]
        result.update(tabular(records))
        result.update(geometry_quality(features))
        result.update(
            crs=CRS.from_wkt(path.with_suffix(".prj").read_text()).to_string(),
            bounds=list(reader.bbox),
            source_fields=[list(f) for f in reader.fields[1:]],
            sample=records[:2],
            countries=dict(Counter(r.get("Country", "unknown") for r in records)),
        )
    elif path.suffix.lower() == ".json":
        value = json.loads(data)
        if value.get("type") == "FeatureCollection":
            features = value["features"]
            result.update(tabular([f["properties"] for f in features]))
            result.update(geometry_quality(features))
            result.update(
                crs=value.get(
                    "crs", "GeoJSON coordinates; EPSG:4326 convention, verify upstream"
                ),
                sample=[f["properties"] for f in features[:1]],
            )
    elif path.suffix.lower() == ".csv":
        raw = data.decode("utf-8-sig", errors="replace")
        result["encoding_replacements"] = raw.count("\ufffd")
        records = list(csv.DictReader(raw.splitlines()))
        result.update(tabular(records))
        result["sample"] = records[:1]
        result["classification"] = "historical outcomes (not negative examples)"
    elif path.suffix.lower() in {".tif", ".tiff"}:
        with rasterio.open(path) as raster:
            result.update(
                crs=str(raster.crs),
                bounds=list(raster.bounds),
                width=raster.width,
                height=raster.height,
                bands=raster.count,
                dtypes=list(raster.dtypes),
                nodata=raster.nodata,
                resolution=list(raster.res),
                tags=raster.tags(),
                missing="NoData sentinel recorded; whole-raster missing-cell scan not performed",
                duplicate_rows="not applicable",
            )
    elif path.suffix.lower() == ".pdf":
        pdf = PdfReader(path)
        result["pages"] = len(pdf.pages)
        result["text"] = "\n".join(p.extract_text() or "" for p in pdf.pages)
    elif path.suffix.lower() == ".xml":
        root = ET.fromstring(data)
        result["metadata"] = [
            {"tag": n.tag.split("}")[-1], "text": (n.text or "").strip()}
            for n in root.iter()
            if (n.text or "").strip()
            and n.tag.split("}")[-1]
            in {
                "CharacterString",
                "Date",
                "DateTime",
                "attrlabl",
                "attrdef",
                "attrunit",
                "attrdefs",
                "title",
                "abstract",
                "useLimit",
            }
        ]
    elif path.suffix.lower() in {".prj", ".cpg"}:
        result["text"] = data.decode("utf-8", errors="replace")
    else:
        result["role"] = (
            "Shapefile sidecar; integrity recorded by SHA-256; interpreted with parent shapefile"
        )
    return result


def main():
    output = ROOT / "backend/data/processed"
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted((ROOT / "data").rglob("*")):
        if not path.is_file():
            continue
        try:
            record = inspect(path)
        except Exception as exc:  # noqa: BLE001 - audit must record any unreadable dataset and continue
            record = {
                "path": path.relative_to(ROOT).as_posix(),
                "error": type(exc).__name__ + ": " + str(exc),
            }
        records.append(record)
        print(record["path"], record.get("records", ""), record.get("error", ""))
    report = {"datasets": records, "originals_modified": False}
    (output / "data-quality.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    rows = [
        "# Local dataset audit",
        "",
        "Generated by `backend/scripts/inspect_datasets.py`. All source files read only. Detailed schemas, missing values, geometry errors, metadata text and SHA-256 hashes are in the ignored `backend/data/processed/data-quality.json`.",
        "",
        "| File | Bytes | Records | CRS | Geometry errors |",
        "|---|---:|---:|---|---:|",
    ]
    for r in records:
        rows.append(
            f"| {r['path']} | {r.get('bytes', '?')} | {r.get('records', '—')} | {r.get('crs', '—')} | {len(r.get('invalid_geometries', [])) if 'invalid_geometries' in r else '—'} |"
        )
    (ROOT / "docs/data-audit.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
