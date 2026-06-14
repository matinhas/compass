# Compass — Next Actions

## Immediate (before v0.1 is live)

- [ ] Copy `.env.example` → `.env` and fill in real values
- [ ] Push to GitHub: `git push origin master`
- [ ] Create Railway project linked to `github.com/matinhas/compass`
- [ ] Add PostgreSQL service in Railway
- [ ] Set Railway env vars: `DATABASE_URL`, `CLICKUP_API_KEY`, `CLICKUP_INBOX_LIST_ID`
- [ ] Verify Railway deploy succeeds and `/health` returns `{"status": "ok"}`
- [ ] Test `POST /captures` end-to-end and confirm ClickUp task appears in Inbox

## v0.2 — AI Classification

- [ ] Add `category`, `urgency`, `tags` columns to captures table (new Alembic migration)
- [ ] Create `app/services/classifier.py` — calls Claude API to classify capture content
- [ ] Run classifier async after capture is stored (non-blocking)
- [ ] Expose classification in `GET /captures` response

## v0.3 — Daily Briefing

- [ ] Add scheduled job (Railway cron or APScheduler) to generate daily summary
- [ ] Summarise all UNPROCESSED captures from last 24h
- [ ] Send briefing to configured channel (ClickUp task / email / webhook)

## v0.4 — Compass Self-Reports

- [ ] Hook git commits to update ClickUp task status via `TASK-XXX` in commit message
- [ ] Auto-update `docs/compass-state.yaml` on each build milestone
