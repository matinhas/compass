# Compass Build Log

> **Operating Rule:** After every meaningful coding session — update this file, update `compass-state.yaml`, commit and push.
> Paste `compass-state.yaml` to ChatGPT to sync architecture and get next steps.

---

## 2026-06-14 — Session 1: MVP-001 Scaffold + Railway Deploy

### Completed
- FastAPI skeleton (`app/main.py`)
- PostgreSQL connection via SQLAlchemy 2.0 (`app/database/db.py`)
- `GET /health` endpoint
- `POST /captures` — stores capture, fires ClickUp task creation (fire-and-forget)
- `GET /captures` — returns all captures newest-first
- Pydantic v2 schemas (`app/schemas/capture.py`)
- SQLAlchemy ORM model with `CAP-00001` formatted capture IDs (`app/models/capture.py`)
- ClickUp Inbox integration via httpx (`app/services/clickup.py`)
- Alembic migration scaffold + first migration (`alembic/versions/001_create_captures_table.py`)
- Railway deployment config (`railway.json` — nixpacks, auto-runs `alembic upgrade head`)
- Dockerfile
- Living docs: `docs/architecture.md`, `docs/build-log.md`, `docs/next-actions.md`, `compass-state.yaml`
- GitHub repo: `github.com/matinhas/compass` (branch: `main`)
- Railway: DATABASE_URL linked to PostgreSQL service, Alembic connecting successfully

### Decisions
- SQLAlchemy 2.0 (`DeclarativeBase`, not legacy `declarative_base`)
- ClickUp failure is fire-and-forget — capture creation never blocked by ClickUp
- Capture ID is human-readable: `CAP-{id:05d}` derived from integer PK (not stored in DB)
- Alembic owns schema — no `create_all` in app startup
- Railway start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Branch renamed from `master` → `main` to match Railway expectation

### In Progress
- Railway first deploy — Alembic connected, awaiting migration completion confirmation

### Next Session Should Start With
1. Confirm Railway URL returns `{"status": "ok"}` on `GET /health`
2. Test `POST /captures` end-to-end and verify ClickUp Inbox task created
3. Add `CLICKUP_API_KEY` and `CLICKUP_INBOX_LIST_ID` to Railway env vars
