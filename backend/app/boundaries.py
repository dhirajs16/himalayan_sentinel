"""Pinned, redistributable map context; never serve the unverified raw copies."""

from pathlib import Path

BOUNDARY_DIR = Path(__file__).resolve().parents[1] / "assets/boundaries"
BOUNDARY_LICENSE = "https://creativecommons.org/licenses/by/4.0/"
BOUNDARY_SOURCE = "https://localboundries.oknp.org/about/"
BOUNDARY_ATTRIBUTION = (
    "Administrative boundaries: Open Knowledge Nepal, LocalBoundaries, CC BY 4.0. "
    "https://localboundries.oknp.org/"
)
BOUNDARY_LIMITATIONS = (
    "Districts are dissolved from local-level boundaries. Repository revision "
    "2026-07-04; survey date unspecified. Geographic context, not certified "
    "emergency jurisdiction or a flood footprint. Source geometry unchanged."
)


def boundary_path(kind, directory=BOUNDARY_DIR):
    if kind not in {"districts", "provinces"}:
        raise ValueError("Unknown boundary level")
    return Path(directory) / f"{kind}.json"


def boundary_attribution(directory=BOUNDARY_DIR):
    return (
        BOUNDARY_ATTRIBUTION
        if Path(directory).resolve() == BOUNDARY_DIR.resolve()
        else "Custom input boundaries; source and rights must be verified separately."
    )
