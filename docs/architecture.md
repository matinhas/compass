# Compass Architecture

## Overview

Compass is a personal capture pipeline. Any source (ChatGPT, browser, CLI, mobile) sends a payload to the `/captures` endpoint. Compass stores it in PostgreSQL and creates a task in the ClickUp Inbox.

## Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Runtime     | Python 3.12                       |
| API         | FastAPI + Uvicorn                 |
| Database    | PostgreSQL (Railway managed)      |
| ORM         | SQLAlchemy 2.0                    |
| Migrations  | Alembic                           |
| HTTP client | httpx (async)                     |
| Validation  | Pydantic v2                       |
| Deploy      | Railway (nixpacks)                |
| Source      | github.com/matinhas/compass       |

## Project Structure

```
compass/
├── app/
│   ├── api/capture.py          — FastAPI router: POST /captures, GET /captures
│   ├── database/db.py          — Engine, session, Base, get_db dependency
│   ├── models/capture.py       — SQLAlchemy ORM model + capture_id property
│   ├── schemas/capture.py      — Pydantic request/response schemas
│   ├── services/
│   │   ├── capture_service.py  — Business logic (create + list captures)
│   │   └── clickup.py          — ClickUp API v2 task creation
│   └── main.py                 — App factory, GET /health
├── alembic/
│   ├── env.py                  — Reads DATABASE_URL from env
│   └── versions/001_*.py       — Creates captures table
├── docs/                       — Living project documentation
├── tests/
├── .env.example
├── Dockerfile
└── railway.json
```

## Data Model

### captures

| Column          | Type        | Notes                        |
|-----------------|-------------|------------------------------|
| id              | Integer PK  | Auto-increment               |
| source          | String      | e.g. "chatgpt", "web"        |
| content         | Text        | Raw capture text             |
| status          | Enum        | UNPROCESSED / PROCESSED      |
| created_at      | DateTime    | UTC, server default          |
| clickup_task_id | String      | Nullable — set after sync    |

`capture_id` is a computed property: `CAP-{id:05d}` (not stored in DB).

## API

| Method | Path       | Description                        |
|--------|------------|------------------------------------|
| GET    | /health    | Liveness check                     |
| POST   | /captures  | Create capture + ClickUp Inbox task|
| GET    | /captures  | List all captures (newest first)   |

### POST /captures

Request:
```json
{ "source": "chatgpt", "content": "Review accountant report" }
```

Response (201):
```json
{
  "capture_id": "CAP-00001",
  "source": "chatgpt",
  "content": "Review accountant report",
  "status": "UNPROCESSED",
  "created_at": "2026-06-14T10:00:00",
  "clickup_task_id": "abc123"
}
```

## Environment Variables

| Variable               | Required | Description                    |
|------------------------|----------|--------------------------------|
| DATABASE_URL           | Yes      | PostgreSQL connection string   |
| CLICKUP_API_KEY        | Yes      | Personal API token from ClickUp|
| CLICKUP_INBOX_LIST_ID  | Yes      | Target list ID in ClickUp      |

## Planned Phases

- **v0.1** — Capture + ClickUp Inbox (current)
- **v0.2** — AI classification (source, urgency, category)
- **v0.3** — Daily Briefing engine
- **v0.4** — Compass self-reports to ClickUp
