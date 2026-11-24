from fastapi.testclient import TestClient

from jarvis.api import app
from jarvis.db import connect, initialize
from jarvis.workforce import seed_workforce


def setup_module():
    initialize()
    # Test with isolated path configured by the project test command/environment.
    seed_workforce()


def test_workforce_has_one_thousand_agents_and_supervisors():
    with connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0] == 1000
        assert conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 10
        assert conn.execute("SELECT COUNT(*) FROM supervisors WHERE level='master'").fetchone()[0] == 10
        assert conn.execute("SELECT COUNT(*) FROM supervisors WHERE level='team'").fetchone()[0] == 100
        assert conn.execute("SELECT COUNT(DISTINCT specialization) FROM agents").fetchone()[0] > 10


def test_task_intake_queues_without_claiming_execution():
    with TestClient(app) as client:
        response = client.post("/api/v1/tasks", json={"request": "Review this Python code and debug the API"})
        assert response.status_code == 202
        task = response.json()
        assert task["status"] == "queued"
        assert task["department_id"] == "engineering"
        assert task["assigned_agent_ids"]
        assert task["plan"][2]["status"] == "not_started"


def test_agent_search_paginates():
    with TestClient(app) as client:
        response = client.get("/api/v1/agents", params={"department": "engineering", "limit": 7})
        assert response.status_code == 200
        assert response.json()["total"] == 100
        assert len(response.json()["items"]) == 7
