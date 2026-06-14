# Compass Build Log

## 2026-06-14

### Completed
- FastAPI skeleton (`app/main.py`)
- PostgreSQL connection via SQLAlchemy 2.0 (`app/database/db.py`)
- `GET /health` endpoint
- `POST /captures` endpoint — stores capture, fires ClickUp task creation
- `GET /captures` endpoint — returns all captures newest-first
- Pydantic v2 schemas (`app/schemas/capture.py`)
- SQLAlchemy ORM model with `CAP-00001` formatted capture IDs (`app/models/capture.py`)
- ClickUp Inbox integration via httpx (`app/services/clickup.py`)
- Alembic migration scaffold + first migration (`alembic/versions/001_create_captures_table.py`)
- Railway deployment config (`railway.json` — nixpacks, auto-runs `alembic upgrade head`)
- Dockerfile
- Initial commit pushed to `github.com/matinhas/compass`

### Decisions
- SQLAlchemy 2.0 (DeclarativeBase, not legacy `declarative_base`)
- ClickUp failure is fire-and-forget — capture creation never blocked by ClickUp
- Capture ID is human-readable: `CAP-{id:05d}` derived from integer PK
- Alembic manages schema (no `create_all` in app startup)
- Railway start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
