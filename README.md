# SolarOps

O&M automation platform for solar plants. Pulls data from SynaptiQ (or any monitoring platform via REST API), transforms it through n8n workflows, and lands structured data in Notion for operations and TimescaleDB for analytics.

**Companion project:** [`solar-monitoring-platform`](../solar-monitoring-platform) — operates at Purdue Level 4/5 only, no OT device connectivity.

---

## What it does

- **W1** — Syncs daily KPIs into Notion + TimescaleDB every morning at 07:00
- **W2** — Syncs asset inventory from SynaptiQ into Notion Assets DB weekly
- **W3** — Triages active alarms by kWp severity → Service Tickets in Notion
- **W4** — Generates PM Tickets with inspection points each quarter
- **W5** — Produces branded PDF monthly reports via Gotenberg
- **W6** — Routes Notion events to ERP / SharePoint / Drive

---

## Quick start

```bash
cp .env.example .env
# Fill in .env values

docker compose up -d
docker compose ps  # all services should be Up (healthy)

curl http://localhost:8000/health
# {"status": "ok", "service": "solarops-mock-api"}

# n8n UI
open http://localhost:5678
```

Then follow `notion/schema.md` to set up the Notion workspace.

---

## Project structure

```
solarops/
├── mock-api/            # FastAPI mock for SynaptiQ API
│   ├── main.py
│   ├── data/            # Static JSON fixtures (devices, kpis, alarms)
│   ├── Dockerfile
│   └── requirements.txt
├── n8n-workflows/       # n8n workflow exports (JSON)
│   ├── W1-daily-kpi.json
│   ├── W2-asset-registry.json
│   ├── W3-alarm-triage.json
│   ├── W4-pm-generator.json
│   ├── W5-pdf-report.json
│   └── W6-event-router.json
├── notion/
│   └── schema.md        # Notion workspace setup guide
├── db/
│   └── schema.sql       # TimescaleDB hypertable + continuous aggregate
├── templates/
│   └── report.html      # Branded PDF HTML template
├── docs/                # ADRs and migration guides
├── docker-compose.yml
├── .env.example
├── .gitignore
├── CLAUDE.md            # Instructions for Claude Code
├── PROJECT_PLAN.md      # Full project plan + workflow definitions
└── SPRINT_PLAN.md       # Current sprint deliverables
```

---

## Stack

| Service | Image | Port |
|---|---|---|
| mock-api | local build | 8000 |
| n8n | n8nio/n8n | 5678 |
| timescaledb | timescale/timescaledb | 5432 |
| gotenberg | gotenberg/gotenberg:8 | 3000 |

All services run on `solarops-net` Docker bridge network. n8n uses TimescaleDB as its own backend database (schema `n8n`), not SQLite.

---

## Switching from mock to real SynaptiQ

1. In n8n → Credentials: update SynaptiQ API URL from `http://mock-api:8000` to the real endpoint
2. Add real SynaptiQ Bearer token
3. Zero workflow code changes required — all endpoints match the mock contract

See `docs/synaptiq-migration.md` when real access is available.
