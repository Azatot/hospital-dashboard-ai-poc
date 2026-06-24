# Codex Handoff

Last updated: 2026-06-24

This project is a hospital dashboard proof of concept with:

- Streamlit frontend on port 8501.
- FastAPI backend on port 8000.
- PostgreSQL database on port 5432.
- Redis on port 6379.
- Adminer on port 8080.

## Repository

Remote:

```powershell
git clone https://github.com/Azatot/hospital-dashboard-ai-poc.git
cd hospital-dashboard-ai-poc
```

Current main branch:

```powershell
master
```

## Run On A New PC

Requirements:

- Git
- Docker Desktop
- Codex

Start the project:

```powershell
docker compose -f docker\docker-compose.yml up --build -d
```

Open:

```text
Dashboard: http://localhost:8501
API docs:  http://localhost:8000/docs
Adminer:   http://localhost:8080
```

Check status and logs:

```powershell
docker compose -f docker\docker-compose.yml ps
docker compose -f docker\docker-compose.yml logs -f
```

Stop the project:

```powershell
docker compose -f docker\docker-compose.yml down
```

## Optional Environment

The project runs without an external AI key by using rule-based fallback logic.

For OpenRouter, create `docker\.env` on the new PC:

```env
OPENROUTER_API_KEY=your_key_here
AI_MODEL=deepseek/deepseek-v4-flash:free
```

Do not commit `.env`; it is ignored by `.gitignore`.

## Database Notes

The Docker database uses a named volume, so Git does not carry local runtime data.

For demo data, a fresh Docker start initializes from:

- `database/schema.sql`
- `docker/seed_data.sql`

If the current PC has important local database data, export it before moving:

```powershell
docker exec hospital-dashboard-db pg_dump -U hospital -d hospital -f /tmp/backup.sql
docker cp hospital-dashboard-db:/tmp/backup.sql .\backup.sql
```

Restore on the new PC after starting Docker:

```powershell
docker cp .\backup.sql hospital-dashboard-db:/tmp/backup.sql
docker exec -it hospital-dashboard-db psql -U hospital -d hospital -f /tmp/backup.sql
```

## Validation Commands

Run these from the repository root:

```powershell
python -m py_compile frontend\app.py
python -m unittest discover -s tests
docker compose -f docker\docker-compose.yml build frontend
```

## Recent Work Summary

Backend and database:

- Hardened SQL execution with read-only validation.
- Improved database connector initialization and driver handling.
- Added configurable CORS, AI model, and Postgres pool settings.
- Made API responses more robust for JSON serialization.
- Improved schema compatibility for generated columns and indexes.

Frontend:

- Redesigned the dashboard header, sidebar, KPI cards, filters, and chart surfaces.
- Simplified the sidebar layout controls.
- Kept detailed KPI and chart reordering inside edit mode.
- Added double-click details for the four main dashboard charts.
- Detail panels show row count, column count, numeric summaries, sample data, and SQL.

Tests:

- Added SQL validation tests under `tests/test_sql_validation.py`.

## Codex Notes

When opening this project in Codex on another PC:

1. Use the repository root as the workspace.
2. Prefer Docker for running the app.
3. Check `git status` before editing.
4. Keep secrets in `docker\.env`, not in tracked files.
5. Use `python -m unittest discover -s tests` before committing backend safety changes.
