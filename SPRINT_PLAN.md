# Sprint Plan — Phase 0: Foundation Setup & Alignment

**Goal:** A clean local-first stack aligned to the Notion-first direction, plus a
documented 7-DB Notion workspace and a passing health check.
**Duration:** Days 1–2
**Status:** Not started
**Roadmap ref:** `PROJECT_PLAN.md` → Implementation Phases, Days 1–2

---

## Deliverables

### Docker stack (target state for this sprint)
- [ ] `docker-compose.yml` services: mock-api + n8n + timescaledb + grafana on `solarops-net`
- [ ] Gotenberg **removed** (returns only with the PDF portfolio extension)
- [ ] n8n on **SQLite** (own `n8n_data` volume) — NOT TimescaleDB as backend
- [ ] TimescaleDB minimal: `plant_kpis` schema only; 5432 bound to `127.0.0.1`
- [ ] Grafana added (:3001), provisioning dir reserved for as-code datasource/dashboards
- [ ] Image tags **pinned** (no `:latest`)

### Config & safety
- [ ] `.env.example` — all required vars with placeholders (Notion token, n8n encryption key, DB creds, Grafana admin password)
- [ ] `.gitignore` — `.env`, `n8n_data/`, `__pycache__/`, `.pytest_cache/`, `backups/`
- [ ] No secrets committed (gitleaks-clean from the start)

### Mock API (minimal — endpoints expand Days 3–5)
- [ ] `mock-api/main.py` — `/health` endpoint only
- [ ] `mock-api/Dockerfile` — multi-stage, non-root
- [ ] Pinned deps in `mock-api/requirements.txt` (migrates to `pyproject.toml` Days 3–5)

### Notion workspace (documented and created in Phase 0–1)
- [ ] 7 DBs per `PROJECT_PLAN.md`: Plants, Assets, Daily Performance, Service Tickets,
      PM Tickets, Reports, Workflow Runs / Audit Log
- [ ] `Plant` modeled as **Relation → Plants** (not a free-text Select)
- [ ] Notion integration token (`secret_xxx`) added to n8n Credentials store
- [ ] All 7 DB IDs added to `.env` (placeholders in `.env.example`)

### Flagged cleanup (execution within this sprint)
- [ ] Remove stray `{docs,mock-api` directory (brace-expansion artifact from prior session)

---

## Validation Gate

```bash
# 1. Stack starts cleanly — 4 services, no Gotenberg
docker compose up -d
docker compose ps
# Expected: mock-api, n8n, timescaledb, grafana all Up (healthy); no gotenberg container

# 2. Mock API responds
curl http://localhost:8000/health
# Expected: {"status": "ok", "service": "solarops-mock-api"}

# 3. n8n UI accessible
open http://localhost:5678
# Expected: n8n login page

# 4. Grafana UI accessible
open http://localhost:3001
# Expected: Grafana login page

# 5. n8n backend is SQLite — not TimescaleDB
docker exec solarops-n8n ls /home/node/.n8n/database.sqlite
# Expected: /home/node/.n8n/database.sqlite (file exists)

# 6. TimescaleDB does NOT have an n8n schema
docker exec solarops-timescaledb psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "\dn" | grep n8n
# Expected: (no rows) — n8n schema absent

# 7. 5432 is NOT exposed to 0.0.0.0
docker compose port timescaledb 5432
# Expected: 127.0.0.1:5432 (not 0.0.0.0:5432)

# 8. n8n reaches mock-api (run from n8n Execute Workflow node)
# HTTP Request node: GET http://mock-api:8000/health
# Expected: {"status": "ok", "service": "solarops-mock-api"}
```

**Most likely failure:** n8n can't reach mock-api.
**Fix:** Confirm both services are on `solarops-net`. Use service name `mock-api`, not `localhost`, inside n8n nodes.

**Second most likely failure:** n8n volume permission error on startup.
**Fix:** The `n8n_data` volume is owned by the n8n image's non-root user (`node`, uid 1000). Ensure no root-owned files exist in the volume from a prior run. `docker compose down -v` removes the volume for a clean retry.

---

## Next Sprint

**Phase 1 — Mock API endpoints (Days 3–5)**

- `/v1/plants` — plant list endpoint
- `/v1/plants/{id}/devices` — asset list per plant
- `mock-api/data/plants.json`, `mock-api/data/devices.json` — seed data
- Migrate to `pyproject.toml` with pinned deps
- pytest for health + new endpoints
- Minimal CI pipeline green (lint, pytest, `docker compose config`)
