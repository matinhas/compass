# Compass Build Log

---

## 2026-06-15 — Session 5: MVP-006.1 Complete + MVP-006 Executive Dashboard

### Completed

**MVP-006.1 — Roadmap Synchronization (verified complete)**
- `app/services/roadmap_sync.py` — `RoadmapSyncService.sync()` reads compass-state.yaml, diffs against ClickUp, creates/updates tasks
- `app/api/sync.py` — `POST /sync/roadmap` endpoint
- `app/schemas/sync.py` — `RoadmapSyncResponse`
- Prefix-key matching (`[MVP-XXX]`) — prevents duplicates on name drift or renames
- Status mapping: `planned→to do`, `active→in progress`, `complete→complete`
- Idempotent: re-run returns `unchanged=12`
- 12 tasks live in ClickUp roadmap list (901218805750)
- `CLICKUP_ROADMAP_LIST_ID` added to Railway

**MVP-006 — Executive Dashboard**
- `app/schemas/dashboard.py` — `DashboardResponse`, `DashboardTopItem`
- `app/services/dashboard.py` — aggregates from PostgreSQL: critical/high counts, captures_today, source_breakdown, domain_breakdown, top_attention (top 5 by attention score)
- `app/api/dashboard.py` — `GET /dashboard`
- Reuses `_score()` from attention service — no duplication
- No ClickUp queries — Compass DB is sole source

### Roadmap Updates
- MVP-006 added to roadmap (active), MVP-006.1 moved to complete
- CMP-001 (Roadmap Synchronization) → complete; CMP-004 (Executive Dashboard) → active

### Next Session Should Start With
1. Validate `GET /dashboard` in production after push
2. Run `POST /sync/roadmap` to reflect MVP-006.1 complete + MVP-006 active in ClickUp
3. MVP-005.3 Izibizi integration

---

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
