"""Explicit development boot for Compose; production never seeds demo users."""

import os
import sys

from .config import ROOT, settings
from .workflow import initialize


def main():
    initialize()
    if settings.environment == "development":
        from .scripts.seed_demo import seed

        seed()
        if list((ROOT / "data").rglob("PDGLs.shp")):
            sys.path.insert(0, str(ROOT / "backend/scripts"))
            from import_geospatial_data import import_data

            import_data()
        from .context_data import import_context

        import_context()
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
    )


if __name__ == "__main__":
    main()
