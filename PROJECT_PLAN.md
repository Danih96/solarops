# SolarOps — O&M Automation Platform

> **Owner:** Daniel
> **Type:** Portfolio + learning project (local-first, finishable)
> **Companion to:** `solar-monitoring-platform` (separate; SolarOps is Purdue L4/5 only)
> **Authority:** This file is the roadmap. Scope changes require explicit user request.

---

## Vision

A local-first O&M back-office automation demo. n8n workflows consume a mock
SynaptiQ-style API and maintain Notion as the operational system of record, while
a minimal TimescaleDB + Grafana layer provides KPI analytics. The project doubles
as a DevOps/DevSecOps showcase.

**End state (demo):** `make up` from a fresh clone brings up the stack. Workflows
sync plants and assets, compute daily KPIs with expected-vs-actual energy, triage
alarms into Service Tickets, and log every run to an Audit Log — with CI, security
scans, and a validated backup/restore story.

---

## Architecture

```
mock-api (FastAPI, read-only)  ──HTTP GET──▶  n8n (orchestration, :5678)
                                                │
   ┌────────────────────────────────────────────┼───────────────────────┐
   ▼ operational truth                           ▼ analytics truth
 Notion (7 DBs)                          TimescaleDB (:5432, minimal)
 Plants · Assets · Daily Perf            plant_kpis (hypertable)
 Service · PM · Reports · Audit Log      [+ workflow_runs optional]
                                                │
                                                ▼
                                         Grafana (:3001, as-code)

DevOps/DevSecOps: GitHub Actions · Makefile · gitleaks · pip-audit ·
hadolint · (Trivy/Syft portfolio tier) · backup/export scripts · optional Ansible
```

**Purdue position:** Level 4/5 only. Read-only consumption. No commands toward L0–3.

---

## Stack

| Component | Technology | Port | Notes |
|---|---|---|---|
| Mock API | FastAPI (Python 3.12) | 8000 | read-only, swappable for real API |
| Workflow engine | n8n self-hosted | 5678 | workflows exported as JSON |
| Operational DB | Notion (7 DBs) | cloud | system of record |
| Analytics DB | TimescaleDB | 5432 (localhost-bound) | KPI series only |
| Dashboard | Grafana | 3001 | datasource + dashboards as code |

> **Decision — n8n backend DB (MVP):** n8n runs on its **own SQLite volume**
> (`n8n_data`). Chosen for the local-first MVP because it keeps TimescaleDB
> minimal and dedicated to KPI time-series/Grafana, and because the n8n state is a
> single file that is trivial to back up/export.
> **n8n does NOT use TimescaleDB as its backend.**
> *Later production option:* move n8n to a **dedicated Postgres** database (its own
> instance, not TimescaleDB) if multi-user/scale requires it.
>
> **Removed from MVP compose:** Gotenberg (returns only with the PDF extension).

---

## Notion Workspace — 7 Databases

> Rule: `Plant` is a **Relation → Plants** everywhere (not a free-text Select).

### DB 1 — Plants
*Plant Registry / source of truth for plant metadata. The spine every other DB relates to.*

Plant Name (Title) · Plant ID (Text, join key, unique) · Owner/Asset Manager
(Text) · Location (Text) · Country (Select) · Timezone (Select) · Installed
Capacity kWp (Number) · SLA Tier (Select) · O&M Provider (Select) · Status
(Select: Active/Commissioning/Decommissioned) · Go-live Date (Date)

### DB 2 — Assets
Name (Title) · Asset Type (Select) · **Plant (Relation → Plants)** · Vendor
(Select) · Rated Power kWp (Number) · Serial Number (Text) · SynaptiQ Device ID
(Text, join key) · Status (Select) · Installed Date (Date) · Last Seen (Date, W2)

### DB 3 — Daily Performance  *(expected-vs-actual)*
Name (Title) · **Plant (Relation → Plants)** · Date (Date) · Actual Energy kWh
(Number, API) · Irradiance kWh/m² (Number, API) · Availability % (Number, API) ·
PR % (Number) · **Expected Energy kWh (n8n)** · **Variance kWh (n8n)** ·
**Variance % (n8n)** · **Estimated Revenue Loss (n8n)** · **Underperformance Flag
(Checkbox, n8n)** · **Underperformance Reason (Select, n8n)** · Status (Select)

### DB 4 — Service Tickets
Name (Title) · Alarm ID (Text, dedup key) · Asset (Relation → Assets) · **Plant
(Relation → Plants)** · Severity (Select) · kWp Affected (Number) · Alarm Type
(Select) · Detected/Acknowledged/Resolved At (Date) · Status (Select) · Root Cause
(Text) · Action Taken (Text)

### DB 5 — PM Tickets  *(later workflow, schema defined now)*
Name (Title) · **Plant (Relation → Plants)** · PM Type (Select) · Scheduled Date
(Date) · Status (Select) · Assets (Relation → Assets) · Inspection Points (Number)

### DB 6 — Reports  *(later workflow, schema defined now)*
Name (Title) · **Plant (Relation → Plants)** · Period (Select) · Report Date
(Date) · Status (Select) · PDF Link (URL) · Delivered To (Email)

### DB 7 — Workflow Runs / Audit Log
Run Name (Title) · Workflow Name (Select) · Run ID (Text, n8n execution id) ·
Trigger Type (Select) · Started At / Finished At (Date+time) · Status (Select:
Success/Partial/Failed) · Records Processed/Created/Updated/Skipped (Number, n8n) ·
Error Message (Text, W-Err) · Correlation ID (Text) · Source Endpoint (Text) ·
Target System (Select: Notion/TimescaleDB/Both) · Plant (Relation → Plants)

---

## Expected vs Actual Energy — MVP formula

```
Expected Energy = Installed Capacity (kWp) × Irradiance (kWh/m²) × PR_target  (PR_target = 0.80)
Variance kWh    = Actual − Expected
Variance %      = Variance / Expected × 100
Revenue Loss    = max(0, −Variance kWh) × tariff   (tariff configurable, e.g. 0.10 €/kWh)
Underperf Flag  = Variance % ≤ −10%
Underperf Reason (n8n Switch): Availability<95% → "Availability loss";
   PR<0.70 & avail OK → "Soiling/degradation"; very low irradiance → "Low resource";
   else → "Investigate"
```
**Ticket rule:** a single-day flag stays in Daily Performance (no ticket). A Service
Ticket is created only when **Variance % ≤ −15% on two consecutive days** (severity
by kWp affected, reusing W3 triage). Separates *signal* from *work order*.

---

## TimescaleDB — minimal schema

`plant_kpis` (hypertable): time, plant_id, energy_kwh, expected_kwh, pr_pct,
availability_pct, irradiance, correlation_id. *(Optional later: `workflow_runs`
metrics for an automation-health dashboard.)* No duplication of Notion records.
TimescaleDB is analytics-only and is never the application database.

---

## n8n Workflows

| ID | Workflow | MVP | Trigger | Flow |
|---|---|---|---|---|
| W-Reg | Plant Registry Sync | ✅ | Manual/weekly | `GET /v1/plants` → upsert Plants (dedup on Plant ID) |
| W2 | Asset Registry Sync | ✅ | Weekly/manual | `GET /v1/plants/{id}/devices` → upsert Assets (dedup on Device ID) |
| W1 | Daily KPI + Expected/Actual | ✅ | 07:00 daily | `GET .../kpis` → compute expected-vs-actual → Notion Daily Perf + TimescaleDB |
| W3 | Alarm Triage | ✅ | every 15 min | `GET .../alarms` → kWp triage + 2-day underperf rule → Service Tickets |
| W-Err | Global Error Workflow | ✅ | n8n error trigger | catch failure → write `Failed` row to Audit Log |
| (Audit) | Audit logging | ✅ | sub-pattern | each workflow writes one Audit Log row at end |
| W4 | PM Generator | 🔶 later | quarterly | active assets → PM Ticket + inspection points |
| W5 | PDF Report (Gotenberg) | 🔶 later | monthly | aggregate → HTML → Gotenberg → Reports |
| W6 | Event Router | ❌ later | Notion webhook | route to ERP/SharePoint/Drive |

**Triage:** kWp ≥ 100 = Critical · ≥ 50 = High · ≥ 10 = Medium · < 10 = Low.
**Dedup keys:** Plants → Plant ID; Assets → SynaptiQ Device ID; Service Tickets → Alarm ID.

---

## DevOps / DevSecOps

**Makefile:** `setup · up · down · test · lint · validate · security · backup · restore-check`

**CI (PRs, minimal):** Python lint → pytest (mock-api) → `docker compose config` →
n8n workflow JSON validation → gitleaks → pip-audit.
**CI (portfolio tier):** + hadolint, Trivy fs+image, Syft SBOM artifact, pinned
Action SHAs, least-privilege `GITHUB_TOKEN`, compose smoke test.

**Security baseline:** `.env` ignored / `.env.example` committed · non-root mock-api ·
pinned image tags (digests portfolio tier) · no Docker socket mount · 5432 bound to
localhost · n8n encryption key in `.env`, credentials never exported with secrets.

---

## Backup / Export

`scripts/`: `export-notion.py` (7 DBs → JSON) · `export-n8n.sh` (workflows +
creds metadata, no secrets; SQLite state is a single file) · `backup-db.sh`
(`pg_dump plant_kpis`) · `export-grafana.sh` · `backup.sh` (orchestrate,
timestamped) · `restore-check.sh` (JSON parses, checksums, row counts > 0,
workflow round-trip).

```
backups/YYYYMMDD-HHMMSS/{notion,n8n,timescaledb,grafana,reports}/  metadata.json
```

Every backup task ships with a validation command.

---

## Implementation Phases (30 days)

| Days | Phase | Gate |
|---|---|---|
| 1–2 | Foundation cleanup | compose fixed (drop Gotenberg, n8n→SQLite, add Grafana, pin images, bind 5432, remove stray dir); `make up` clean |
| 3–5 | Mock API endpoints | `/health`, `/v1/plants`, `/devices`; `pyproject.toml`; pytest; minimal CI green |
| 6–8 | Notion 7 DBs + W-Reg + W2 | Plants spine, relations, Audit Log DB; dedup tested |
| 9–12 | W1 + Expected/Actual + TimescaleDB | `plant_kpis` hypertable; formula in n8n; dual-write; 30 days simulated |
| 13–15 | Grafana | datasource + 1 dashboard as code (energy, variance, availability) |
| 16–18 | W3 Alarm Triage + perf ticket rule | `/alarms`, kWp triage, 2-day underperf ticket, dedup tested |
| 19–20 | W-Err + Audit wiring | every workflow logs a run; failures recorded |
| 21–23 | Backup/export | `make backup` + `make restore-check` pass with metadata |
| 24–26 | DevSecOps portfolio tier | Trivy, Syft SBOM, gitleaks pre-commit, pinned SHAs, least-priv token |
| 27–28 | Docs + runbooks | architecture, security-boundary, devops, backup-restore, demo-guide; fresh-clone README |
| 29–30 | Polish + optional Ansible | demo script; minimal Ansible bring-up if time; tag v1.0 |

---

## Architectural Decisions

| Decision | Choice | Rejected | Reason |
|---|---|---|---|
| Automation engine | n8n self-hosted | Make, Zapier | Self-hostable, JSON export, no per-execution cost |
| n8n backend DB (MVP) | SQLite (own volume) | TimescaleDB, Postgres | Keeps TimescaleDB minimal; single-file backup; local-first |
| n8n backend DB (later) | Dedicated Postgres | — | Production option if multi-user/scale needs it (not TimescaleDB) |
| Operational DB | Notion | Airtable, custom | Client-familiar, mature API, ticket/record-centric |
| Analytics DB | TimescaleDB (minimal) | Notion for series | Time-series + Grafana; Notion can't store series |
| Mock API | FastAPI | Static JSON in n8n | Realistic, easy swap to real API |
| Dual KPI output | Notion + TimescaleDB | One only | Notion for operators, Grafana for analysis |
| Secrets | .env + n8n Credentials | Plain text | Minimum viable security for local dev |

---

## Scope Summary

**MVP:** Plants · Assets (W2) · Daily KPI + Expected/Actual (W1) · Alarm Triage (W3) ·
Error Workflow (W-Err) · Audit Log · TimescaleDB KPI series · 1 Grafana dashboard ·
backup/export · minimal CI + gitleaks/pip-audit/hadolint · Security Boundary doc.

**Portfolio extension:** PM Generator (W4) · PDF Reports (W5, Gotenberg) ·
Trivy/Syft/pinned-SHA tier · Ansible · automation-health dashboard · pinned image
digests · n8n on dedicated Postgres.

**Out of scope:** OT/Purdue L0–3 · Azure/Terraform/Kubernetes · multi-tenant SaaS ·
real SynaptiQ until stable · Event Router/ERP/SharePoint/Drive · Claude API agent ·
SIEM · trading/market data.

---

## Open Items

- Confirm Notion plan webhook availability (free = polling; Business = native webhooks)
- Decide tariff + PR_target source (constant now → Plants field later)
- When real API access arrives: document endpoints in `docs/synaptiq-migration.md`
