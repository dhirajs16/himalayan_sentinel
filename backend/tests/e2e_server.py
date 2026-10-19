"""Isolated browser-test service; never opens the application's local database."""

import os
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
(root / "var").mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="sentinel-e2e-", dir=root / "var") as directory:
    os.environ["DATABASE_URL"] = "sqlite:///" + (Path(directory) / "test.db").as_posix()
    os.environ["STORAGE_DIR"] = str(Path(directory) / "evidence")
    os.environ["WEATHER_LIVE"] = "false"
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["CORS_ORIGINS"] = "http://127.0.0.1:3100,http://localhost:3100"
    from app.scripts.seed_demo import seed
    from app.workflow import initialize

    initialize()
    seed()
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8010)
