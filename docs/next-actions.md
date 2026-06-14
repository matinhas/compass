# Compass — Next Actions

## Now: Finish MVP-001 Deploy

- [ ] Confirm Railway deploy succeeds — `GET /health` returns `{"status": "ok"}`
- [ ] Add `CLICKUP_API_KEY` to Railway env vars (compass service → Variables)
- [ ] Add `CLICKUP_INBOX_LIST_ID` to Railway env vars
- [ ] Test end-to-end: `POST /captures` → capture stored → ClickUp Inbox task appears
- [ ] MVP-001 complete ✓

---

## MVP-002 — Inbox Classification

- [ ] Add `category`, `urgency`, `tags` columns to captures (new Alembic migration)
- [ ] Create `app/services/classifier.py` — calls Claude API to classify capture content
- [ ] Run classifier async after capture is stored (non-blocking, like ClickUp)
- [ ] Classification types: Task, Project, Decision, Reference, Alert
- [ ] Expose classification fields in `GET /captures` response

## MVP-003 — Daily Briefing

- [ ] Add scheduled job (Railway cron or APScheduler) — runs once daily
- [ ] Summarise all UNPROCESSED captures from last 24h
- [ ] Send briefing to configured output (ClickUp task / email / webhook)

## MVP-004 — Attention Engine

- [ ] Score each capture by urgency, recency, source weight
- [ ] `GET /captures?ranked=true` returns prioritised list
- [ ] Surface top 3 items needing attention

## MVP-005 — Integrations

- [ ] Gmail — watch inbox, create captures from flagged emails
- [ ] respond.io — create captures from flagged conversations
- [ ] Izibizi — accounting alerts → captures
- [ ] WordPress — comments / contact form → captures
