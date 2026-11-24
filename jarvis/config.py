"""Configuration loaded from environment without logging secrets."""
from __future__ import annotations

import os
from pathlib import Path

DB_PATH = Path(os.getenv("JARVIS_DB_PATH", "./data/jarvis.sqlite3"))
API_KEY = os.getenv("JARVIS_API_KEY")
