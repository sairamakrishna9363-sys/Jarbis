"""Seed the scalable logical workforce (profiles, not running model processes)."""
from __future__ import annotations

from jarvis.db import connect, json_value

DEPARTMENTS = [
    ("research", "Research & Intelligence", "Research, source evaluation, evidence and reporting", ["research", "sources", "fact checking", "analysis", "reporting"]),
    ("engineering", "Software Engineering", "Software design, implementation, review and debugging", ["python", "software", "api", "debugging", "architecture"]),
    ("security", "Cybersecurity", "Authorized defensive security and secure development", ["defensive security", "secure code", "risk", "audit", "privacy"]),
    ("design", "Design & Creativity", "Accessible product design and creative workflows", ["ui design", "ux", "accessibility", "branding", "prototyping"]),
    ("ai_ml", "AI & Machine Learning", "Model integration, evaluation and AI systems", ["machine learning", "model evaluation", "llm", "retrieval", "ai integration"]),
    ("android", "Android & Personal Automation", "Permission-based mobile integrations and automation", ["android", "accessibility APIs", "mobile", "notifications", "device permissions"]),
    ("analytics", "Data & Analytics", "Data analysis, processing and reporting", ["data analysis", "statistics", "sql", "visualization", "data quality"]),
    ("quality", "Testing & Quality Assurance", "Software validation, testing and reliability", ["testing", "quality", "regression", "api testing", "validation"]),
    ("infrastructure", "Infrastructure & DevOps", "Infrastructure, delivery, monitoring and recovery", ["linux", "ci/cd", "containers", "monitoring", "backup"]),
    ("learning", "Knowledge, Learning & Evolution", "Evidence-based knowledge and controlled improvement", ["knowledge management", "verification", "skill evaluation", "memory", "learning"]),
]

def seed_workforce() -> None:
    with connect() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        if existing:
            return
        # Insert department/supervisor records first; references are enforced by SQLite.
        for dept_id, name, description, _ in DEPARTMENTS:
            master_id = f"sup-{dept_id}-master"
            conn.execute("INSERT INTO departments VALUES (?, ?, ?, ?)", (dept_id, name, description, master_id))
            conn.execute("INSERT INTO supervisors (id,name,level,department_id,team_number,reports_to) VALUES (?,?,?,?,?,?)",
                         (master_id, f"{name} Master Supervisor", "master", dept_id, None, "jarvis-core"))
            for team in range(1, 11):
                sup_id = f"sup-{dept_id}-{team:02d}"
                conn.execute("INSERT INTO supervisors (id,name,level,department_id,team_number,reports_to) VALUES (?,?,?,?,?,?)",
                             (sup_id, f"{name} Team Supervisor {team:02d}", "team", dept_id, team, master_id))
        for dept_id, dept_name, _, skills in DEPARTMENTS:
            for index in range(100):
                team = index // 10 + 1
                specialization = skills[index % len(skills)]
                agent_id = f"agent-{dept_id}-{index + 1:03d}"
                conn.execute(
                    "INSERT INTO agents (id,name,role,department_id,team_number,supervisor_id,specialization,skills_json,permissions_json,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (agent_id, f"{dept_name} Specialist {index + 1:03d}", specialization.title(), dept_id,
                     team, f"sup-{dept_id}-{team:02d}", specialization,
                     json_value([specialization, dept_name.lower()]),
                     json_value(["read:task", "read:knowledge", "propose:action"]), "idle"),
                )
