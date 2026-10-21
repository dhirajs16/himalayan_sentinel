"""Synthetic geography proves filtering, chronology and count-raster semantics."""

import csv
import hashlib
import json

import numpy as np
import pytest
import rasterio
import shapefile
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pyproj import CRS
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

from app import context_api
from app.context_data import (
    POPULATION_PRODUCT,
    ContextStore,
    event_date,
    import_context,
)


def write_boundaries(data, features):
    target = data / "GeoJson/districts.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"DISTRICT": name},
                        "geometry": mapping(geometry),
                    }
                    for name, geometry in features
                ],
            }
        ),
        encoding="utf-8",
    )
    return target


def write_lakes(data):
    target = data / "inventory/GL_3basins_2015.shp"
    target.parent.mkdir(parents=True)
    with shapefile.Writer(str(target)) as writer:
        for name in ("GL_ID", "Country", "Basin"):
            writer.field(name, "C", 40)
        writer.poly([[[0.5, 0.5], [0.5, 1.5], [1.5, 1.5], [1.5, 0.5], [0.5, 0.5]]])
        writer.record("A", "Nepal", "Koshi")
        # Its centre lies outside Rasuwa, but the polygon intersects the district.
        writer.poly([[[1.9, 0.5], [1.9, 1.5], [5, 1.5], [5, 0.5], [1.9, 0.5]]])
        writer.record("B", "China", "Koshi")
        writer.null()
        writer.record("C", "Nepal", "Gandaki")
    target.with_suffix(".prj").write_text(CRS.from_epsg(4326).to_wkt())


def write_events(data, revision, rows):
    target = data / "historical" / f"HMAGLOFDB v{revision}_13122025.csv"
    target.parent.mkdir(exist_ok=True)
    fields = [
        "GF_ID",
        "Lat_lake",
        "Lon_lake",
        "Year_exact",
        "Year_approx",
        "Month",
        "Day",
        "Lake_name",
        "Country",
        "River_Basin",
        "Impact",
    ]
    with target.open("w", encoding="cp1252", newline="") as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**dict.fromkeys(fields, "NA"), **row})


@pytest.fixture
def context(tmp_path):
    data, output = tmp_path / "data", tmp_path / "processed"
    data.mkdir()
    write_boundaries(
        data, [("Rasuwa", box(0, 0, 2, 2)), ("Gorkha", box(10, 10, 12, 12))]
    )
    write_lakes(data)
    write_events(data, "3.0", [{"GF_ID": "1", "Lake_name": "Old revision"}])
    write_events(
        data,
        "4.0",
        [
            {
                "GF_ID": "1",
                "Lat_lake": "1",
                "Lon_lake": "1",
                "Year_exact": "2024",
                "Year_approx": "2024",
                "Month": "7",
                "Day": "6",
                "Lake_name": "Lake café",
                "Country": "Nepal",
                "River_Basin": "Koshi",
                "Impact": "Reported damage\nsecond line",
            },
            {"GF_ID": "2", "Year_approx": "1900", "Lake_name": "Approximate"},
            {
                "GF_ID": "3",
                "Lat_lake": "nan",
                "Lon_lake": "inf",
                "Lake_name": "Unknown date",
            },
        ],
    )
    original = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in data.rglob("*")
        if p.is_file()
    }
    summary = import_context(data, output, boundary_dir=data / "GeoJson")
    assert summary == {"lakes": 3, "events": 3, "districts": 2}
    assert original == {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in data.rglob("*")
        if p.is_file()
    }
    return ContextStore(data, output, boundary_dir=data / "GeoJson")


def test_import_latest_revision_dates_unmapped_and_geometry(context):
    events = context.query("events")["items"]
    assert [row["id"] for row in events] == ["hmaglof:1", "hmaglof:2", "hmaglof:3"]
    assert events[0]["name"] == "Lake café"
    assert events[0]["date"] == "2024-07-06"
    assert events[0]["date_precision"] == "day"
    assert events[0]["impact"] == "Reported damage\nsecond line"
    assert events[1]["year"] == "1900" and events[1]["date"] is None
    assert events[1]["date_precision"] == "approximate_year"
    assert events[2]["year"] is None and events[2]["geometry"] is None
    assert events[2]["lat"] is None and events[2]["lng"] is None
    assert events[0]["properties"]["GF_ID"] == "1"
    assert events[0]["source_date"] == "2025-12-13"
    assert context.query("lakes", district="Rasuwa")["total"] == 2
    assert context.query("lakes", district="Gorkha")["total"] == 0
    assert context.query("lakes", country="NEPAL", basin="Koshi")["total"] == 1
    assert context.query("events", q="CAFÉ")["total"] == 1
    assert context.query("events", district="rasuwa")["total"] == 1
    assert (
        context.query("lakes", offset=1, limit=1)["items"][0]["id"]
        == "icimod-inventory:B"
    )
    assert context.query("lakes")["items"][2]["geometry"] is None
    assert "Rank" not in context.query("lakes")["items"][0]["properties"]


@pytest.mark.parametrize(
    ("properties", "expected"),
    [
        ({"Year_exact": "2023", "Month": "2", "Day": "31"}, ("2023-02", "month")),
        ({"Year_exact": "2023", "Month": "NA"}, ("2023", "year")),
        (
            {"Year_exact": "NA", "Year_approx": "before 1900"},
            (None, "approximate_year"),
        ),
        ({"Year_exact": "NA", "Year_approx": "NA"}, (None, "unknown")),
    ],
)
def test_date_precision_preserves_partial_or_unknown(properties, expected):
    result = event_date(properties)
    assert (result["date"], result["date_precision"]) == expected


def write_population(data, values, verified=True):
    path = data / POPULATION_PRODUCT
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=values.shape[1],
        height=values.shape[0],
        count=1,
        dtype="float32",
        crs=CRS.from_epsg(4326).to_wkt(),
        nodata=-99999,
        transform=from_origin(85, 29, 1 / 1200, 1 / 1200),
    ) as raster:
        raster.write(values.astype("float32"), 1)
        if verified:
            raster.update_tags(
                TIFFTAG_DOCUMENTNAME=path.stem,
                TIFFTAG_IMAGEDESCRIPTION="NPL population 2026 [WorldPop R2025A v1]",
                TIFFTAG_COPYRIGHT="CC-BY-4.0",
            )
    return path


def test_population_counts_masking_bounded_extent_and_cache_invalidation(tmp_path):
    data, output = tmp_path / "data", tmp_path / "processed"
    data.mkdir()
    step = 1 / 1200
    geometry = box(85, 29 - 2 * step, 85 + 4 * step, 29)
    write_boundaries(data, [("Rasuwa", geometry), ("Outside", box(0, 0, 1, 1))])
    values = np.array(
        [[10, 20, -99999, np.nan], [30, -1, 0, np.inf], [500, 500, 500, 500]]
    )
    write_population(data, values)
    store = ContextStore(data, output, boundary_dir=data / "GeoJson")
    result = store.population("rasuwa")
    assert result["status"] == "ready"
    assert result["population"] == 60  # count per pixel: never multiply by pixel area
    assert result["valid_cells"] == 4 and result["selected_cells"] == 8
    assert result["cache"] == "miss"
    assert store.population("Rasuwa")["cache"] == "hit"
    assert store.population("outside")["status"] == "no_coverage"
    old_key = result["source_fingerprints"]
    values[0, 0] = 11
    write_population(data, values)
    updated = store.population("rasuwa")
    assert updated["population"] == 61 and updated["cache"] == "miss"
    assert updated["source_fingerprints"] != old_key
    write_boundaries(data, [("Rasuwa", box(85, 29 - step, 85 + 4 * step, 29))])
    changed_boundary = store.population("rasuwa")
    assert changed_boundary["population"] == 31 and changed_boundary["cache"] == "miss"
    assert changed_boundary["valid_cells"] == 2
    assert "flood exposure" in changed_boundary["limitations"]
    assert not list(output.rglob("*.tmp"))


def test_population_rejects_unverified_product_and_missing_data(tmp_path):
    data = tmp_path / "data"
    write_boundaries(data, [("Rasuwa", box(85, 28, 86, 29))])
    store = ContextStore(data, tmp_path / "processed", boundary_dir=data / "GeoJson")
    assert store.population("rasuwa")["status"] == "unavailable"
    write_population(data, np.ones((3, 3)), verified=False)
    result = store.population("rasuwa")
    assert result["status"] == "unverified" and result["population"] is None
    with pytest.raises(KeyError):
        store.population("invented district")


def test_context_routes_bound_queries_and_missing_states(
    context, monkeypatch, tmp_path
):
    app = FastAPI()
    app.include_router(context_api.router)
    monkeypatch.setattr(context_api, "store", context)
    with TestClient(app) as client:
        prefix = "/api/v1/public/context"
        result = client.get(
            prefix + "/lakes", params={"district": "rasuwa", "offset": 1, "limit": 1}
        )
        assert result.status_code == 200 and result.json()["total"] == 2
        assert len(result.json()["items"]) == 1
        for params in [
            {"limit": 101},
            {"offset": -1},
            {"limit": 0},
            {"q": "x" * 151},
            {"country": "x" * 81},
        ]:
            assert client.get(prefix + "/events", params=params).status_code == 422
        assert client.get(prefix + "/population/nonexistent").status_code == 404
        catalog = client.get(prefix + "/catalog").json()
        assert len(catalog["districts"]) == 2
        assert catalog["sources"][1]["count"] == 3
        assert str(context.data_dir) not in json.dumps(catalog)
        assert (
            client.get(prefix + "/population/rasuwa").json()["status"] == "unavailable"
        )
        monkeypatch.setattr(
            context_api,
            "store",
            ContextStore(
                tmp_path / "missing",
                tmp_path / "unprepared",
                boundary_dir=tmp_path / "missing-boundaries",
            ),
        )
        assert client.get(prefix + "/events").json()["total"] == 0
        assert (
            client.get(prefix + "/catalog").json()["sources"][0]["status"]
            == "unavailable"
        )


def test_processed_file_replacement_refreshes_query(context):
    assert context.query("events")["total"] == 3
    path = context.processed_dir / "context.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["events"] = []
    path.write_text(json.dumps(document), encoding="utf-8")
    assert context.query("events")["total"] == 0


def test_public_boundaries_use_licensed_bundle_and_preserve_source(system):
    from app.boundaries import BOUNDARY_DIR, BOUNDARY_LICENSE, boundary_path

    manifest = json.loads((BOUNDARY_DIR / "manifest.json").read_text())
    for entry in manifest["files"]:
        kind = entry["file"].removesuffix(".json")
        response = system.get(f"/api/v1/public/boundaries/{kind}")
        assert response.status_code == 200
        assert BOUNDARY_LICENSE in response.headers["link"]
        assert hashlib.sha256(response.content).hexdigest() == entry["sha256"]
        assert len(response.json()["features"]) == entry["features"]
        assert boundary_path(kind).parent == BOUNDARY_DIR
    catalog = ContextStore().catalog()
    source = next(s for s in catalog["sources"] if s["id"] == "boundaries")
    assert source["count"] == 77
    assert "Open Knowledge Nepal" in source["attribution"]
    assert "CC BY 4.0" in source["attribution"]
    assert system.get("/api/v1/public/boundaries/unknown").status_code == 422
