"""SQLite persistence for the initial JARVIS core."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from jarvis.config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS departments (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
  master_supervisor_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS supervisors (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, level TEXT NOT NULL,
  department_id TEXT NOT NULL REFERENCES departments(id), team_number INTEGER,
  reports_to TEXT
);
CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL,
  department_id TEXT NOT NULL REFERENCES departments(id), team_number INTEGER NOT NULL,
  supervisor_id TEXT NOT NULL REFERENCES supervisors(id), specialization TEXT NOT NULL,
  skills_json TEXT NOT NULL, permissions_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'idle', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_agents_department ON agents(department_id);
CREATE INDEX IF NOT EXISTS idx_agents_specialization ON agents(specialization);
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY, request TEXT NOT NULL, status TEXT NOT NULL,
  department_id TEXT REFERENCES departments(id), plan_json TEXT NOT NULL,
  assigned_agent_ids_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
"""

@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)

def json_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)

def decode_row(row: sqlite3.Row, json_columns: tuple[str, ...] = ()) -> dict:
    result = dict(row)
    for key in json_columns:
        result[key.removesuffix("_json")] = json.loads(result.pop(key))
    return result
