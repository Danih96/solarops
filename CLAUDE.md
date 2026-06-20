# CLAUDE.md — SolarOps

## 1. Project Goal

Build a local-first O&M automation platform for solar plants using:

FastAPI mock API → n8n workflows → Notion operational database → minimal TimescaleDB analytics layer → Grafana dashboard.

The project is a portfolio and learning project designed to demonstrate:

* solar O&M back-office automation
* Notion-based operational workflows
* n8n workflow orchestration
* API integration with FastAPI
* basic time-series analytics with TimescaleDB and Grafana
* DevOps delivery practices
* DevSecOps checks
* backup/export and restore thinking
* clear IT/OT boundary awareness

SolarOps should be useful, realistic, and finishable. Avoid turning it into a large SaaS, cloud, Kubernetes, or OT integration project.

## 2. Source of Truth

Roadmap: `PROJECT_PLAN.md`

Current sprint: `SPRINT_PLAN.md`

Follow the current sprint exactly. Do not redesign, expand scope, or add new components unless the user explicitly asks.

## 3. Architecture Direction

SolarOps is Notion-first.

Main components:

* `mock-api`: FastAPI service that simulates a SynaptiQ-like solar data API
* `n8n`: workflow automation engine
* `Notion`: main operational database and system of record
* `TimescaleDB`: minimal analytics layer for KPI time-series only
* `Grafana`: dashboard for KPI and platform visibility
* `GitHub Actions`: CI, validation, and DevSecOps checks
* `backup/export scripts`: Notion snapshots, n8n workflow exports, Grafana dashboard exports, TimescaleDB dump
* `Ansible`: optional local/VM deployment skill booster

Notion is used for operational data.

TimescaleDB is used only where time-series storage makes sense, mainly KPI history and Grafana analytics.

## 4. Purdue / OT Boundary

SolarOps operates only at Purdue Level 4/5.

This is non-negotiable.

SolarOps must not connect to:

* PLCs
* inverters
* meters
* relays
* RTUs
* SCADA servers
* plant control networks
* Modbus
* OPC-UA
* MQTT brokers
* IEC 104
* any Purdue Level 0-3 systems

SolarOps only consumes data from:

* the local FastAPI mock API
* later, a real external business/API layer if available
* exported datasets

SolarOps must never send commands to plant equipment.

SolarOps must not have any command/control capability.

## 5. Scope — What This Project Builds

In scope for the main project:

* FastAPI mock server
* Docker Compose local stack
* n8n self-hosted workflows
* Notion databases:

  * Plants
  * Assets
  * Daily Performance
  * Service Tickets
  * PM Tickets
  * Reports
  * Workflow Runs / Audit Log
* minimal TimescaleDB schema for KPI analytics
* Grafana dashboard
* expected vs actual energy logic
* alarm triage logic
* workflow audit logging
* global n8n error workflow
* GitHub Actions CI
* DevSecOps scans
* backup/export scripts
* security boundary documentation
* README, runbooks, and demo guide

Optional skill booster:

* Ansible deployment to a local VM or lab host

## 6. What NOT to Build

Do not build:

* direct OT integrations
* Modbus, OPC-UA, MQTT, IEC 104, SunSpec, or SCADA connectors
* Azure infrastructure
* Terraform deployment
* AKS or Kubernetes
* multi-tenant SaaS architecture
* mobile apps
* HMI screens
* trading algorithms
* energy market integrations
* full SIEM integration
* complex IAM platform
* real SynaptiQ integration until the mock API and workflows are stable
* Claude API agent integration in the MVP

PDF reports, ERP integration, SharePoint integration, Drive integration, and AI agent features are later extensions, not MVP requirements.

## 7. MVP Scope

The MVP should prove the platform works end-to-end.

MVP includes:

* Docker Compose stack starts locally
* FastAPI health endpoint works
* Notion databases are documented and created
* Plant Registry exists
* Asset Registry Sync workflow works
* Daily KPI Sync workflow works
* Expected vs Actual Energy logic works
* Alarm Triage workflow creates Service Tickets
* Workflow Runs / Audit Log is written by workflows
* minimal TimescaleDB KPI table receives KPI data
* Grafana dashboard reads from TimescaleDB
* GitHub Actions CI validates code and config
* basic DevSecOps scans run
* backup/export scripts exist
* security boundary document exists

## 8. Later Scope

Later extensions may include:

* PM ticket generator
* monthly PDF reports with Gotenberg
* report delivery tracking
* Event Router
* SharePoint or Drive delivery
* ERP mock integration
* advanced Grafana dashboard
* Ansible deployment
* restore automation
* more advanced DevSecOps checks

Do not implement later-scope items unless explicitly requested.

## 9. Notion Data Model Rules

Notion is the operational database.

Prefer relation fields over duplicated select values when one entity depends on another.

Plants should be a dedicated database and should be referenced by:

* Assets
* Daily Performance
* Service Tickets
* PM Tickets
* Reports

Workflow Runs / Audit Log should track workflow execution status and errors.

Daily Performance should include expected vs actual energy fields.

Service Tickets should be created only when there is a meaningful operational issue, such as critical alarm, underperformance, or platform failure.

## 10. TimescaleDB Rules

TimescaleDB must stay minimal.

Use it for:

* KPI time-series
* Grafana analytics
* optional workflow metrics if needed later

Do not duplicate the entire Notion operational data model into TimescaleDB.

Do not make TimescaleDB the main application database.

## 11. DevOps Rules

The project should be reproducible from a fresh clone.

Prefer clear commands through a `Makefile` or equivalent task runner.

Expected commands should include:

```bash
make setup
make up
make down
make test
make lint
make validate
make security
make backup
```

GitHub Actions should validate the project on pull requests.

Minimum CI checks:

* Python linting
* FastAPI tests
* Docker Compose config validation
* n8n workflow JSON validation
* secret scanning
* dependency scanning

Stronger portfolio checks may include:

* Trivy scan
* Hadolint
* SBOM generation
* pinned GitHub Actions
* least-privilege workflow permissions

## 12. DevSecOps Rules

No secrets in git.

Required:

* `.env` ignored
* `.env.example` committed
* Notion tokens never committed
* n8n credentials never exported with secrets
* database passwords only through environment variables
* GitHub Actions must use least-privilege permissions
* no Docker socket mount
* minimal exposed ports
* Docker networks separated where useful
* non-root containers where realistic
* pinned dependency versions

Security tooling should be practical, not excessive.

Start with:

* gitleaks
* pip-audit or equivalent
* Trivy
* Docker Compose validation

Add later if useful:

* Hadolint
* Syft SBOM
* Grype
* SOPS or age
* Infisical, Vault, Doppler, or Bitwarden Secrets Manager

## 13. Backup / Export Rules

The project must include backup/export thinking.

Backup/export scope:

* Notion database snapshots through API export scripts
* n8n workflow exports
* n8n credentials metadata without secrets, if possible
* minimal TimescaleDB dump
* Grafana dashboard JSON
* generated reports, if PDF reports are implemented
* sanitized config files

Backups should be stored under a predictable local folder, for example:

```text
backups/
  YYYYMMDD-HHMMSS/
    notion/
    n8n/
    timescaledb/
    grafana/
    reports/
    metadata.json
```

Every backup task must include a validation command.

## 14. How to Help During Implementation

Follow this working style:

1. Explain what should change and why.
2. Wait for user approval before editing or generating implementation code.
3. Work on one task at a time.
4. Keep changes small and reviewable.
5. Avoid bundling unrelated work.
6. After each task, provide:

   * diff summary
   * validation command
   * expected result
   * most likely failure
   * 2 quiz questions for learning

## 15. Code Generation Rules

Use:

* Python 3.12
* FastAPI
* Pydantic validation
* pinned dependencies in `pyproject.toml`
* Docker Compose for local development
* exported n8n workflows as JSON

Rules:

* no hardcoded secrets
* no undocumented manual UI steps
* no comments unless the reason is not obvious
* no large rewrites unless explicitly requested
* no broad refactors during feature work
* no generated files committed unless required and documented

## 16. n8n Rules

n8n workflows must be exported as JSON.

Each workflow should document:

* trigger
* input source
* transformation logic
* target system
* deduplication key
* audit log behavior
* error behavior
* validation steps

Workflows should be idempotent where possible.

Each production-like workflow should write to Workflow Runs / Audit Log.

A global Error Workflow should be added once the first core workflows exist.

## 17. Commit Message Rules

Use Conventional Commits.

Examples:

```text
feat(mock-api): add plant devices endpoint
feat(notion): document plant registry schema
feat(n8n): add asset registry sync workflow
feat(audit): add workflow runs database schema
feat(ci): add docker compose validation
feat(security): add gitleaks scan
fix(n8n): correct service ticket deduplication
docs(security): add Purdue boundary document
chore: update docker compose healthchecks
```

## 18. Validation Rules

Every implementation task must include:

* exact command to run
* expected output or pass/fail criterion
* most likely failure
* how to fix the most likely failure

Validation should prefer local commands that the user can run directly.

## 19. Documentation Rules

Maintain documentation as the project evolves.

Expected docs:

* `README.md`
* `PROJECT_PLAN.md`
* `SPRINT_PLAN.md`
* `docs/architecture.md`
* `docs/notion-schema.md`
* `docs/security-boundary.md`
* `docs/devops.md`
* `docs/backup-restore.md`
* `docs/runbooks/`
* `docs/demo-guide.md`

Do not let implementation drift away from documentation.