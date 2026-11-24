"""HTTP API for JARVIS core foundation."""
from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from jarvis.config import API_KEY
from jarvis.db import connect, decode_row, initialize
from jarvis.orchestrator import list_tasks, submit_task
from jarvis.workforce import seed_workforce

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    seed_workforce()
    yield

app = FastAPI(title="JARVIS Core", version="0.1.0", description="Permission-aware agent workforce and task intake foundation.", lifespan=lifespan)

async def authorize(authorization: Annotated[str | None, Header()] = None) -> None:
    if API_KEY:
        expected = f"Bearer {API_KEY}"
        if not authorization or not secrets.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="A valid bearer token is required.")

Auth = Annotated[None, Depends(authorize)]

class TaskRequest(BaseModel):
    request: str = Field(min_length=1, max_length=10_000)

@app.get("/health")
def health():
    return {"status": "ok", "service": "jarvis-core", "execution": "task intake only"}

@app.get("/api/v1/departments", dependencies=[Depends(authorize)])
def departments():
    with connect() as conn:
        rows = conn.execute("SELECT d.*, (SELECT COUNT(*) FROM agents a WHERE a.department_id=d.id) AS agent_count, (SELECT COUNT(*) FROM supervisors s WHERE s.department_id=d.id) AS supervisor_count FROM departments d ORDER BY d.id").fetchall()
    return [dict(row) for row in rows]

@app.get("/api/v1/agents", dependencies=[Depends(authorize)])
def agents(department: str | None = None, search: str | None = None,
           limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    conditions, params = [], []
    if department:
        conditions.append("department_id=?"); params.append(department)
    if search:
        conditions.append("(name LIKE ? OR specialization LIKE ? OR role LIKE ?)")
        params.extend([f"%{search}%"] * 3)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM agents {where} ORDER BY id LIMIT ? OFFSET ?", (*params, limit, offset)).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM agents {where}", params).fetchone()[0]
    return {"total": total, "items": [decode_row(row, ("skills_json", "permissions_json")) for row in rows]}

@app.get("/api/v1/supervisors", dependencies=[Depends(authorize)])
def supervisors(department: str | None = None):
    with connect() as conn:
        if department:
            rows = conn.execute("SELECT * FROM supervisors WHERE department_id=? ORDER BY level,team_number", (department,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM supervisors ORDER BY department_id,level,team_number").fetchall()
    return [dict(row) for row in rows]

@app.post("/api/v1/tasks", status_code=202, dependencies=[Depends(authorize)])
def create_task(body: TaskRequest):
    return submit_task(body.request)

@app.get("/api/v1/tasks", dependencies=[Depends(authorize)])
def tasks(limit: int = Query(default=50, ge=1, le=200)):
    return list_tasks(limit)
