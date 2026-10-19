"""Prepare optional local context without modifying original files or DB tables."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.context_data import import_context

if __name__ == "__main__":
    print(json.dumps(import_context(), indent=2))
