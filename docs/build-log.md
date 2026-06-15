# Compass Build Log

---

## 2026-06-15 — Session 9: Attention Filtering

### Completed

**Attention Filtering — classification + engine + dashboard**

- `alembic/versions/004_add_attention_fields.py` — migration adds `attention_required` (Boolean) and `attention_reason` (Text) to captures table
- `app/models/capture.py` — two new columns added
- `app/services/classifier.py` — prompt extended: AI now returns `attention_required` bool and `attention_reason` string alongside existing fields; `ClassificationResult` updated; safe fallback on missing key
- `app/services/capture_service.py` — persists `attention_required` + `attention_reason` from classification result
- `app/services/attention.py` — `generate_attention_ranking` now queries `attention_required = True` only
- `app/services/dashboard.py` — all dashboard counts (critical, high, captures_today, source/domain breakdown, top_attention) now filter to `attention_required = True` only

### Behaviour
- `attention_required = true`: customer complaints, approval requests, supplier decisions, accountant requests, legal issues, operational risk
- `attention_required = false`: newsletters, promotions, receipts, system notifications, marketing emails
- Pre-migration captures (NULL) are excluded from filtered views — conservative default
- Running the migration on Railway via `alembic upgrade head` on next deploy

### Next Session Should Start With
1. Validate in production: new captures classified with attention_required field
2. Check dashboard counts drop to reflect actionable items only
3. MVP-005.3: Izibizi integration

---

## 2026-06-15 — Session 8: MVP-006 Layer Complete — MCP + ClickUp Mirror + Dashboard

### Completed

**MVP-006.2 — Compass MCP Server (COMPLETE)**
- Added `get_system_status()` MCP tool: checks database, roadmap_sync, gmail, respondio; returns environment + overall health + version
- Logic extracted to `app/services/system_status.py`; MCP tool delegates to service (no duplication)
- Verified: 7 tools registered, no direct external service imports in MCP tools layer
- Verified: all tools callable, server starts cleanly

**MVP-006.3 — ClickUp Operational Mirror (COMPLETE)**
- Verified idempotency: two consecutive syncs produce 0 created, 1 updated (STATUS description refresh), 19 unchanged — no drift
- All ClickUp objects present: [FOCUS], [STATUS], all [MVP-XXX], all [CMP-XXX]

**MVP-006 — Executive Dashboard (expanded)**
- Added `roadmap_progress: int` — % of roadmap milestones complete
- Added `system_health: str` — reuses `check_system_health()` from system_status service
- `app/schemas/dashboard.py` — two new fields
- `app/services/dashboard.py` — computes both fields; imports service layer only
- Dashboard is now the primary human-facing Compass entry point

### Architecture
- `app/services/system_status.py` — health check service (single source of truth)
- `app/mcp/tools/system_status.py` — delegates to service (MCP interface)
- `app/services/dashboard.py` — calls service directly (no MCP layer coupling)

### Roadmap Updates
- MVP-006.2 → complete
- MVP-006.3 → complete
- CMP-005 → complete
- CMP-006 → complete
- current_focus → MVP-006 (Executive Dashboard)

### Next Session Should Start With
1. Validate GET /dashboard in production returns all 10 fields including roadmap_progress + system_health
2. Confirm /mcp endpoint accessible at production URL
3. MVP-006 final sign-off once dashboard validated in production
4. MVP-005.3: Izibizi integration

---

## 2026-06-15 — Session 7: MVP-006.3 ClickUp Operational Mirror

### Completed

**MVP-006.3 — ClickUp Operational Mirror**

Extended `app/services/roadmap_sync.py`:
- `sync_focus()` — creates/maintains single `[FOCUS] <name>` task in roadmap list; updates name if focus changes; idempotent
- `sync_status_summary()` — creates/maintains `[STATUS] Compass Project Status` task; description auto-generated from roadmap layer progress (Foundation Layer ✅ / Integrations % / Operations Layer %) plus current focus and next milestone; always refreshed on sync
- `_add_comment()` — posts ClickUp comment on task; called by `_sync_list` when status transitions `non-complete → complete`; format: "Milestone completed by Compass Sync. Date: YYYY-MM-DD"
- `_create_task()` — now accepts optional `description`
- `_update_task()` — now accepts optional `description`
- `sync()` — now calls all four sync stages: roadmap → commitments → focus → status summary

Extended `GET /dashboard`:
- `app/schemas/dashboard.py` — added `current_focus: str`, `active_commitments: int`, `completed_milestones: int`
- `app/services/dashboard.py` — loads compass-state.yaml to populate new fields; reuses YAML path pattern; no DB duplication

### compass-state.yaml Updates
- `MVP-006.3: ClickUp Operational Mirror` → active
- `CMP-006: ClickUp Operational Mirror` → active
- `current_focus` → MVP-006.3
- Architecture decisions updated

### Roadmap Updates
- MVP-006.3 added (active)
- CMP-006 added (active)

### Next Session Should Start With
1. Validate `[FOCUS]` and `[STATUS]` tasks appear in ClickUp after deploy + sync
2. Validate dashboard returns `current_focus`, `active_commitments`, `completed_milestones`
3. MVP-006.2: confirm `/mcp/sse` accessible in production
4. MVP-005.3: Izibizi integration

---

## 2026-06-15 — Session 6: MVP-006 Dashboard Validated + MVP-006.2 Compass MCP Server

### Completed

**MVP-006 — Executive Dashboard (validated)**
- `GET /dashboard` deployed and live in production
- Returns critical/high counts, captures_today, source/domain breakdowns, top 5 attention items

**MVP-006.2 — Compass MCP Server**
- `app/mcp/server.py` — FastMCP instance with 6 registered tools
- `app/mcp/tools/dashboard.py` — `get_dashboard` (DB → DashboardResponse)
- `app/mcp/tools/briefing.py` — `get_briefing` (DB → daily briefing summary)
- `app/mcp/tools/attention.py` — `get_attention` (DB → top 10 scored items)
- `app/mcp/tools/roadmap.py` — `get_roadmap` (compass-state.yaml → key/status map)
- `app/mcp/tools/commitments.py` — `get_commitments` (YAML) + `sync_roadmap` (→ ClickUp)
- `app/main.py` — MCP mounted at `/mcp` via `compass_mcp.sse_app()`
- `.mcp.json` — Compass SSE server added: `https://compass-production-2fc4.up.railway.app/mcp/sse`
- `requirements.txt` — `mcp>=1.2.0` added
- All MCP tools use `SessionLocal()` directly (no FastAPI Depends)

### Roadmap Updates
- MVP-006 → complete; MVP-006.2 → active
- CMP-005 (Compass MCP Server) → active

### Next Session Should Start With
1. Push MVP-006.2 to Railway and verify `/mcp/sse` responds
2. Run `POST /sync/roadmap` to update ClickUp with MVP-006.2 active
3. MVP-005.3 Izibizi integration

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
