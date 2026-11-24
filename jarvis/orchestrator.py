"""Conservative task intake and deterministic workforce routing.

This component records a proposed plan and queues work; it does not claim to run
agents, call models, browse the internet, or execute external actions.
"""
from __future__ import annotations

import json
import uuid
from jarvis.db import connect, json_value, decode_row
from jarvis.workforce import DEPARTMENTS

KEYWORDS = {
    "research": ("research", "source", "fact check", "investigate", "paper"),
    "engineering": ("code", "software", "website", "app", "debug", "build", "api"),
    "security": ("security", "secure", "vulnerability", "audit", "privacy"),
    "design": ("design", "logo", "interface", "ui", "ux", "prototype"),
    "ai_ml": ("model", "machine learning", "llm", "ai", "embedding"),
    "android": ("android", "phone", "notification", "mobile"),
    "analytics": ("data", "analyze", "analytics", "statistics", "sql"),
    "quality": ("test", "testing", "validate", "quality", "regression"),
    "infrastructure": ("deploy", "server", "docker", "ci/cd", "backup", "linux"),
    "learning": ("learn", "knowledge", "improve", "skill", "memory"),
}

def classify(request: str) -> str:
    text = request.casefold()
    scores = {dept: sum(1 for word in words if word in text) for dept, words in KEYWORDS.items()}
    # Stable fallback keeps the request actionable without pretending an LLM parsed it.
    best = max(scores, key=scores.get)
    return best if scores[best] else "research"

def submit_task(request: str) -> dict:
    department_id = classify(request)
    task_id = str(uuid.uuid4())
    with connect() as conn:
        selected = conn.execute(
            "SELECT id FROM agents WHERE department_id=? ORDER BY id LIMIT 1", (department_id,)
        ).fetchone()
        agent_ids = [selected["id"]] if selected else []
        plan = [
            {"step": 1, "action": "classify_request", "status": "completed", "method": "keyword routing"},
            {"step": 2, "action": "assign_logical_specialist", "status": "completed" if agent_ids else "blocked"},
            {"step": 3, "action": "execute_request", "status": "not_started", "reason": "No execution provider is configured in this foundation."},
            {"step": 4, "action": "verify_result", "status": "not_started"},
        ]
        conn.execute("INSERT INTO tasks (id,request,status,department_id,plan_json,assigned_agent_ids_json) VALUES (?,?,?,?,?,?)",
                     (task_id, request, "queued", department_id, json_value(plan), json_value(agent_ids)))
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return decode_row(row, ("plan_json", "assigned_agent_ids_json"))

def list_tasks(limit: int = 50) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [decode_row(row, ("plan_json", "assigned_agent_ids_json")) for row in rows]
