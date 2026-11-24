# JARVIS Core

JARVIS is being built in tested, reversible phases. This repository currently contains the **core foundation**: a local FastAPI service, persistent SQLite registry, 1,000 logical agent profiles across ten departments, the requested supervisor hierarchy, searchable agent profiles, and transparent task intake/routing.

This is not yet the complete autonomous ecosystem described in the master specification. In particular, task requests are stored and routed to a logical profile; no AI model, external tool, phone, browser, voice service, or autonomous execution is configured. The API reports this explicitly rather than fabricating completed work.

## Current foundation

- 10 departments, each seeded with 100 distinct logical agent records.
- 10 master supervisors and 100 team supervisors (10 teams of 10 profiles per department).
- SQLite-backed agent and task records; seed is idempotent and only runs on an empty workforce.
- Paginated/filterable agent directory and supervisor/department APIs.
- Deterministic keyword-based task routing. Submitted work remains `queued`; the plan marks execution and verification as not started.
- Optional bearer-token API protection (`JARVIS_API_KEY`). Agents have only read/propose permissions in the initial catalog.

These are profiles, not 1,000 concurrently running model processes. Metrics, learning, and task success are not fabricated or inferred from profile data.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e '.[test]'
cp .env.example .env  # optional; export variables manually or use your preferred dotenv loader
uvicorn jarvis.api:app --host 127.0.0.1 --port 8000
```

The app reads environment variables directly; it does not automatically load `.env`. For a protected instance, set `JARVIS_API_KEY` in the process environment and send `Authorization: Bearer <key>`. Do not expose the unauthenticated development server to an untrusted network. The database is created at `JARVIS_DB_PATH` (default `./data/jarvis.sqlite3`).

## API

- `GET /health` — service health and explicit execution scope.
- `GET /api/v1/departments` — departments and real registry counts.
- `GET /api/v1/agents?department=engineering&search=python&limit=50&offset=0` — searchable, paginated profiles.
- `GET /api/v1/supervisors?department=engineering` — supervisor hierarchy.
- `POST /api/v1/tasks` with `{"request":"Review my Python API"}` — classify, assign a logical specialist and persist a queued plan (HTTP 202); does not execute the request.
- `GET /api/v1/tasks` — recent persisted requests.

Interactive API docs are available at `/docs` while the service is running.

## Tests

```bash
python -m pip install -e '.[test]'
pytest
```

The tests exercise the seeded workforce shape, routing/intake transparency and agent pagination. For isolated tests, set `JARVIS_DB_PATH` to a temporary database path before running pytest.

## Safety and roadmap

External content will be treated as untrusted data. High-impact actions need explicit permissions/approval; unknown software must be evaluated and sandboxed before use. The initial core does not execute shell commands, browse, send messages, access devices, or mutate its own source. A production deployment still needs migrations, robust authentication, audit trails, task workers, provider integrations, approval workflows, observability, backups and security review.

Next implementation phases: richer task planning and durable execution/approval state; memory and provenance-aware knowledge; pluggable model/provider adapters; reviewed tool registry and sandbox; then voice/Android and a responsive command center. Each integration should report unavailable until it is actually configured and tested.
