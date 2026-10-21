"""Read-only geographic context, independent of assessed lakes and alert decisions.

Run scripts/import_context_data.py to prepare licensed local inventory files.
Only derived JSON/cache files are written; application tables and source data are
never changed. All public provenance uses product names, never local paths.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from threading import RLock

import numpy as np
import rasterio
import shapefile
from pyproj import CRS, Transformer
from rasterio.features import geometry_mask, geometry_window
from rasterio.windows import Window
from shapely import transform
from shapely.geometry import Point, mapping, shape
from shapely.strtree import STRtree

from .boundaries import (
    BOUNDARY_DIR,
    BOUNDARY_LIMITATIONS,
    boundary_attribution,
    boundary_path,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = ROOT / "backend/data/processed"
LAKE_ATTRIBUTION = (
    "ICIMOD (2020), Glacial lakes in the Koshi, Gandaki, and Karnali river "
    "basins of Nepal, the Tibet Autonomous Region of China, and India. "
    "https://doi.org/10.26066/RDS.1971946"
)
EVENT_ATTRIBUTION = (
    "ICIMOD (2023), GLOF database of High Mountain Asia. "
    "https://doi.org/10.26066/RDS.1973283"
)
POPULATION_PRODUCT = "npl_pop_2026_CN_100m_R2025A_v1.tif"
POPULATION_DOCUMENTATION = (
    "https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/"
    "doc/Global2_Release_Statement_R2025A_v1.pdf"
)
CONTEXT_LIMITATIONS = (
    "Static geographic and historical context is not a current hazard forecast. "
    "District membership is geometric overlap, not a downstream inundation zone. "
    "Population is modelled district context, not people exposed to a flood."
)
POPULATION_LIMITATIONS = (
    "WorldPop R2025A v1 is an alpha modelled estimate for 2026, not a census "
    "or real-time occupancy count. District totals use pixel centres within "
    "the supplied boundary; boundary differences, NoData and model uncertainty "
    "affect results. This is district context, not flood exposure."
)


def _safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    return value


def _text(value):
    result = str(value).strip() if value is not None else ""
    return (
        None
        if result.lower() in {"", "na", "n/a", "nan", "unknown", "none", "null"}
        else result
    )


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def _atomic_json(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(_safe(document), handle, ensure_ascii=False, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _stamp(path):
    info = Path(path).stat()
    return {"name": Path(path).name, "size": info.st_size, "mtime_ns": info.st_mtime_ns}


def _fingerprint(paths):
    result = []
    for path in paths:
        digest = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        result.append({**_stamp(path), "sha256": digest.hexdigest()})
    return result


def load_districts(path):
    """Return only usable WGS84 district polygons; no synthetic boundaries."""
    path = Path(path)
    if not path.exists():
        return []
    document = json.loads(path.read_text(encoding="utf-8"))
    districts = []
    for feature in document.get("features", []):
        properties = feature.get("properties", {})
        name = _text(properties.get("DISTRICT") or properties.get("name"))
        if not name or not feature.get("geometry"):
            continue
        geometry = shape(feature["geometry"])
        if (
            geometry.is_empty
            or not geometry.is_valid
            or geometry.geom_type not in {"Polygon", "MultiPolygon"}
        ):
            continue
        if not (
            -180 <= geometry.bounds[0] <= geometry.bounds[2] <= 180
            and -90 <= geometry.bounds[1] <= geometry.bounds[3] <= 90
        ):
            continue
        center = geometry.representative_point()
        districts.append(
            {
                "id": _slug(name),
                "name": name,
                "geometry": mapping(geometry),
                "lat": center.y,
                "lng": center.x,
            }
        )
    if len({item["id"] for item in districts}) != len(districts):
        raise ValueError("District source contains duplicate names")
    return sorted(districts, key=lambda item: item["name"])


class DistrictIndex:
    def __init__(self, districts):
        self.districts = districts
        self.tree = STRtree([shape(item["geometry"]) for item in districts])

    def names(self, geometry):
        if geometry is None or geometry.is_empty:
            return []
        return sorted(
            self.districts[int(index)]["id"]
            for index in self.tree.query(geometry, predicate="intersects")
        )


def _record_geometry(geometry, district_index):
    if geometry is None or geometry.is_empty or not geometry.is_valid:
        return {"lat": None, "lng": None, "geometry": None, "district": None}, []
    bounds = geometry.bounds
    if not (
        -180 <= bounds[0] <= bounds[2] <= 180 and -90 <= bounds[1] <= bounds[3] <= 90
    ):
        return {"lat": None, "lng": None, "geometry": None, "district": None}, []
    point = geometry.representative_point()
    districts = district_index.names(geometry)
    return {
        "lat": point.y,
        "lng": point.x,
        "geometry": mapping(geometry),
        "district": districts[0] if districts else None,
    }, districts


def prepare_lakes(path, district_index):
    path = Path(path)
    projection = path.with_suffix(".prj")
    if not projection.exists():
        raise ValueError("Lake source is missing its projection")
    transformer = Transformer.from_crs(
        CRS.from_wkt(projection.read_text()), 4326, always_xy=True
    )
    records, identifiers = [], set()
    with shapefile.Reader(str(path)) as reader:
        fields = [field[0] for field in reader.fields[1:]]
        if not {"GL_ID", "Country", "Basin"} <= set(fields):
            raise ValueError("Lake source is missing GL_ID/Country/Basin")
        for entry in reader.iterShapeRecords():
            properties = _safe(dict(zip(fields, entry.record)))
            source_id = _text(properties.get("GL_ID"))
            if not source_id or source_id in identifiers:
                raise ValueError("Lake source has a missing or duplicate GL_ID")
            identifiers.add(source_id)
            geometry = None
            if entry.shape.shapeType != shapefile.NULL:
                geometry = transform(
                    shape(entry.shape.__geo_interface__),
                    transformer.transform,
                    interleaved=False,
                )
            location, districts = _record_geometry(geometry, district_index)
            records.append(
                {
                    "id": f"icimod-inventory:{source_id}",
                    "name": _text(properties.get("Name")) or source_id,
                    "country": _text(properties.get("Country")),
                    "basin": _text(properties.get("Basin")),
                    **location,
                    "properties": {
                        **properties,
                        "source_id": source_id,
                        "districts": districts,
                        "inventory_imagery_year": 2015,
                    },
                    "attribution": LAKE_ATTRIBUTION,
                    "source_date": "2020-09-10",
                }
            )
    return records


def event_date(properties):
    """Never replace an unknown/approximate date with a fabricated full date."""
    exact = _text(properties.get("Year_exact"))
    approximate = _text(properties.get("Year_approx"))
    if exact is None:
        return {
            "year": approximate,
            "date": None,
            "date_precision": "approximate_year" if approximate else "unknown",
        }
    result = {"year": exact, "date": None, "date_precision": "year"}
    if not re.fullmatch(r"\d{4}", exact) or not 1 <= int(exact) <= 9999:
        result["date_precision"] = "reported_year"
        return result
    result["date"] = exact
    month = _text(properties.get("Month"))
    day = _text(properties.get("Day"))
    if month and month.isdigit() and 1 <= int(month) <= 12:
        result.update(date=f"{exact}-{int(month):02d}", date_precision="month")
        if day and day.isdigit():
            try:
                full_date = date(int(exact), int(month), int(day))
            except ValueError:
                pass
            else:
                result.update(date=full_date.isoformat(), date_precision="day")
    return result


def _point(latitude, longitude):
    try:
        lat, lng = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None
    return (
        Point(lng, lat)
        if math.isfinite(lat)
        and math.isfinite(lng)
        and -90 <= lat <= 90
        and -180 <= lng <= 180
        else None
    )


def _revision(path):
    match = re.search(
        r"v(\d+(?:\.\d+)*)_(\d{2})(\d{2})(\d{4})\.csv$", path.name, re.IGNORECASE
    )
    if not match:
        return None
    version = tuple(int(value) for value in match[1].split("."))
    released = date(int(match[4]), int(match[3]), int(match[2]))
    return version, released


def latest_events(data_dir):
    candidates = [
        (path, _revision(path)) for path in Path(data_dir).rglob("HMAGLOFDB*.csv")
    ]
    candidates = [(path, revision) for path, revision in candidates if revision]
    return max(candidates, key=lambda item: item[1])[0] if candidates else None


def prepare_events(path, district_index):
    path = Path(path)
    # The distributed v4 CSV is Windows-1252, not UTF-8. Decode without data loss.
    payload = path.read_bytes()
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = payload.decode("cp1252")
    reader = csv.DictReader(io.StringIO(text))
    if not {"GF_ID", "Lat_lake", "Lon_lake", "Year_exact", "Year_approx"} <= set(
        reader.fieldnames or []
    ):
        raise ValueError("Historical source is missing required fields")
    records, identifiers = [], set()
    revision = _revision(path)
    source_date = revision[1].isoformat() if revision else None
    for properties in reader:
        source_id = _text(properties.get("GF_ID"))
        if not source_id or source_id in identifiers:
            raise ValueError("Historical source has a missing or duplicate GF_ID")
        identifiers.add(source_id)
        location, districts = _record_geometry(
            _point(properties.get("Lat_lake"), properties.get("Lon_lake")),
            district_index,
        )
        records.append(
            {
                "id": f"hmaglof:{source_id}",
                "name": _text(properties.get("Lake_name"))
                or _text(properties.get("Glacier_name"))
                or f"Historical event {source_id}",
                "country": _text(properties.get("Country")),
                "basin": _text(properties.get("River_Basin")),
                **location,
                **event_date(properties),
                "impact": _text(properties.get("Impact")),
                "properties": {
                    **properties,
                    "source_id": source_id,
                    "source_revision": path.name,
                    "districts": districts,
                },
                "attribution": EVENT_ATTRIBUTION,
                "source_date": source_date,
            }
        )
    return records


def import_context(
    data_dir=DATA_DIR, processed_dir=PROCESSED_DIR, boundary_dir=BOUNDARY_DIR
):
    data_dir, processed_dir = Path(data_dir), Path(processed_dir)
    district_path = boundary_path("districts", boundary_dir)
    districts = load_districts(district_path)
    district_index = DistrictIndex(districts)
    lakes = list(data_dir.rglob("GL_3basins_2015.shp"))
    if len(lakes) > 1:
        raise ValueError(
            "Multiple lake inventories found; choose one unambiguous source"
        )
    events = latest_events(data_dir)
    sources, records = [], {}
    for identifier, name, path, prepare, attribution, limitations in [
        (
            "lakes",
            "ICIMOD glacial-lake inventory (2015 imagery)",
            lakes[0] if lakes else None,
            prepare_lakes,
            LAKE_ATTRIBUTION,
            "Static inventory; no dangerous-lake ranks or live lake measurements. Source licensing applies.",
        ),
        (
            "events",
            "High Mountain Asia historical GLOFs",
            events,
            prepare_events,
            EVENT_ATTRIBUTION,
            "Latest available revision only; incomplete historical coverage, approximate/unknown dates retained. Historical lake locations do not delineate impacted areas.",
        ),
    ]:
        items = prepare(path, district_index) if path else []
        paths = [path] if path else []
        if path and path.suffix == ".shp":
            paths = [
                path.with_suffix(suffix) for suffix in (".shp", ".shx", ".dbf", ".prj")
            ]
        records[identifier] = items
        sources.append(
            {
                "id": identifier,
                "name": name,
                "status": "ready" if path else "unavailable",
                "count": len(items),
                "source_date": items[0]["source_date"] if items else None,
                "attribution": attribution,
                "limitations": limitations,
                "unmapped_count": sum(item["geometry"] is None for item in items),
                "inputs": _fingerprint(paths),
            }
        )
    document = {
        "schema_version": 1,
        "sources": sources,
        "districts": districts,
        **records,
        "boundary_inputs": _fingerprint([district_path])
        if district_path.exists()
        else [],
        "limitations": CONTEXT_LIMITATIONS,
    }
    _atomic_json(processed_dir / "context.json", document)
    return {
        "lakes": len(records["lakes"]),
        "events": len(records["events"]),
        "districts": len(districts),
    }


class ContextStore:
    def __init__(
        self, data_dir=DATA_DIR, processed_dir=PROCESSED_DIR, boundary_dir=BOUNDARY_DIR
    ):
        self.data_dir, self.processed_dir = Path(data_dir), Path(processed_dir)
        self.boundary_dir = Path(boundary_dir)
        self._lock = RLock()
        self._document = None
        self._signature = None
        self._districts = None
        self._district_signature = None
        self._fingerprints = {}

    def _load(self):
        path = self.processed_dir / "context.json"
        signature = tuple(_stamp(path).values()) if path.exists() else None
        with self._lock:
            if signature != self._signature or self._document is None:
                try:
                    self._document = (
                        json.loads(path.read_text(encoding="utf-8"))
                        if signature
                        else {}
                    )
                except (ValueError, OSError):
                    self._document = {}
                self._signature = signature
            return self._document

    def districts(self):
        path = boundary_path("districts", self.boundary_dir)
        signature = tuple(_stamp(path).values()) if path.exists() else None
        with self._lock:
            if signature != self._district_signature or self._districts is None:
                try:
                    self._districts = load_districts(path)
                except (ValueError, OSError):
                    self._districts = []
                self._district_signature = signature
            return self._districts

    def district(self, district_id):
        identifier = _slug(district_id)
        return next(
            (item for item in self.districts() if item["id"] == identifier), None
        )

    def catalog(self):
        document = self._load()
        bundled = self.boundary_dir.resolve() == BOUNDARY_DIR.resolve()
        sources = [
            {key: value for key, value in item.items() if key != "inputs"}
            for item in document.get("sources", [])
        ]
        if not sources:
            sources = [
                {
                    "id": identifier,
                    "name": name,
                    "status": "unavailable",
                    "count": 0,
                    "source_date": None,
                    "attribution": attribution,
                    "limitations": "Local context has not been prepared or is unavailable.",
                }
                for identifier, name, attribution in [
                    ("lakes", "ICIMOD lake inventory", LAKE_ATTRIBUTION),
                    ("events", "Historical GLOF events", EVENT_ATTRIBUTION),
                ]
            ]
        sources.append(
            {
                "id": "boundaries",
                "name": "Nepal district boundaries (Open Knowledge Nepal)"
                if bundled
                else "Custom district boundaries",
                "status": "ready" if self.districts() else "unavailable",
                "count": len(self.districts()),
                "source_date": "2026-07-04 repository revision; survey date unspecified"
                if bundled
                else None,
                "attribution": boundary_attribution(self.boundary_dir),
                "limitations": BOUNDARY_LIMITATIONS
                if bundled
                else "Custom input; verify provenance, geometry and rights independently.",
            }
        )
        sources.append(
            {
                "id": "population",
                "name": "WorldPop 2026 constrained population, R2025A v1",
                "status": "available"
                if (self.data_dir / POPULATION_PRODUCT).exists()
                else "unavailable",
                "count": None,
                "source_date": "2026",
                "attribution": "WorldPop, CC BY 4.0",
                "limitations": POPULATION_LIMITATIONS,
            }
        )
        return {
            "sources": sources,
            "districts": [
                {"id": item["id"], "name": item["name"]} for item in self.districts()
            ],
            "limitations": CONTEXT_LIMITATIONS,
        }

    def query(self, kind, q="", country="", basin="", district="", offset=0, limit=50):
        if kind not in {"lakes", "events"}:
            raise ValueError("Unknown context kind")
        document = self._load()
        rows = document.get(kind, [])
        query, country, basin = (
            q.strip().casefold(),
            country.strip().casefold(),
            basin.strip().casefold(),
        )
        district_id = _slug(district) if district else None
        filtered = []
        for row in rows:
            if country and (row.get("country") or "").casefold() != country:
                continue
            if basin and basin not in (row.get("basin") or "").casefold():
                continue
            if district_id and district_id not in row.get("properties", {}).get(
                "districts", []
            ):
                continue
            if (
                query
                and query
                not in " ".join(
                    str(row.get(field) or "")
                    for field in ("name", "id", "country", "basin", "year", "impact")
                ).casefold()
            ):
                continue
            filtered.append(row)
        return {
            "items": filtered[offset : offset + limit],
            "total": len(filtered),
            "offset": offset,
            "limit": limit,
        }

    def _source_fingerprint(self, path):
        signature = tuple(_stamp(path).values())
        cached = self._fingerprints.get(str(path))
        if cached is None or cached[0] != signature:
            cached = (signature, _fingerprint([path])[0])
            self._fingerprints[str(path)] = cached
        return cached[1]

    def population(self, district_id):
        district = self.district(district_id)
        if district is None:
            raise KeyError("Unknown district")
        result = {
            "status": "unavailable",
            "district": district["name"],
            "district_id": district["id"],
            "population": None,
            "year": 2026,
            "units": "people",
            "attribution": "WorldPop, University of Southampton, CC BY 4.0",
            "source": POPULATION_PRODUCT,
            "documentation": POPULATION_DOCUMENTATION,
            "method": "Sum nonnegative finite people-per-pixel estimates whose pixel centres fall within the district; exclude NoData. No area/density multiplier.",
            "valid_cells": 0,
            "limitations": POPULATION_LIMITATIONS,
            "boundary_attribution": boundary_attribution(self.boundary_dir),
        }
        raster = self.data_dir / POPULATION_PRODUCT
        if not raster.exists():
            return {**result, "reason": "The local population source is unavailable."}
        district_path = boundary_path("districts", self.boundary_dir)
        provenance = {
            "raster": self._source_fingerprint(raster),
            "boundary": self._source_fingerprint(district_path),
            "district_geometry": hashlib.sha256(
                json.dumps(district["geometry"], sort_keys=True).encode()
            ).hexdigest(),
            "method_version": 1,
        }
        cache_key = hashlib.sha256(
            json.dumps(provenance, sort_keys=True).encode()
        ).hexdigest()
        cache_path = (
            self.processed_dir / "population" / f"{district['id']}-{cache_key}.json"
        )
        if cache_path.exists():
            try:
                return {
                    **json.loads(cache_path.read_text(encoding="utf-8")),
                    "cache": "hit",
                }
            except (ValueError, OSError):
                pass
        try:
            with rasterio.open(raster) as dataset:
                tags = dataset.tags()
                description = tags.get(
                    "TIFFTAG_IMAGEDESCRIPTION", tags.get("Description", "")
                )
                document_name = tags.get("TIFFTAG_DOCUMENTNAME", "")
                if (
                    dataset.count != 1
                    or dataset.crs is None
                    or CRS.from_wkt(dataset.crs.to_wkt()).to_epsg() != 4326
                    or "population 2026 [WorldPop R2025A v1]" not in description
                    or document_name != Path(POPULATION_PRODUCT).stem
                    or not math.isclose(
                        abs(dataset.transform.a), 1 / 1200, rel_tol=0.001
                    )
                    or not math.isclose(
                        abs(dataset.transform.e), 1 / 1200, rel_tol=0.001
                    )
                ):
                    return {
                        **result,
                        "status": "unverified",
                        "reason": "Raster metadata does not match the verified WorldPop population-count product.",
                    }
                geometry = district["geometry"]
                try:
                    window = geometry_window(dataset, [geometry]).intersection(
                        Window(0, 0, dataset.width, dataset.height)
                    )
                except rasterio.errors.WindowError:
                    return {
                        **result,
                        "status": "no_coverage",
                        "reason": "District does not overlap the raster.",
                    }
                total, valid_cells, selected_cells = 0.0, 0, 0
                # Bounded 1024x1024 blocks, even for large districts; no country-sized array.
                for row in range(
                    int(window.row_off), int(window.row_off + window.height), 1024
                ):
                    for col in range(
                        int(window.col_off), int(window.col_off + window.width), 1024
                    ):
                        tile = Window(
                            col,
                            row,
                            min(1024, int(window.col_off + window.width) - col),
                            min(1024, int(window.row_off + window.height) - row),
                        )
                        values = dataset.read(1, window=tile, masked=True)
                        inside = geometry_mask(
                            [geometry],
                            out_shape=values.shape,
                            transform=dataset.window_transform(tile),
                            invert=True,
                            all_touched=False,
                        )
                        valid = (
                            inside
                            & ~np.ma.getmaskarray(values)
                            & np.isfinite(values.data)
                            & (values.data >= 0)
                        )
                        selected_cells += int(inside.sum())
                        valid_cells += int(valid.sum())
                        total += float(values.data[valid].sum(dtype=np.float64))
                result.update(
                    status="ready" if valid_cells else "no_coverage",
                    population=round(total, 2) if valid_cells else None,
                    valid_cells=valid_cells,
                    selected_cells=selected_cells,
                    source_fingerprints=provenance,
                    raster_tags=tags,
                    count_units_evidence="WorldPop R2025A v1 release statement pp. 1 and 5: estimated people per grid cell; exact local product identified by embedded TIFF tags.",
                    cache="miss",
                )
        except (rasterio.errors.RasterioError, ValueError, OSError):
            return {
                **result,
                "reason": "Population calculation could not read a valid local source.",
            }
        _atomic_json(cache_path, result)
        return result


store = ContextStore()
