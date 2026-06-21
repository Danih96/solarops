# Sprint Plan — Phase 2: Notion Schema + W-Reg + W2

**Goal:** Full 7-DB Notion workspace documented and n8n workflows W-Reg and W2
exported as importable JSON. Plant and asset registry sync end-to-end.
**Duration:** Days 6–8
**Status:** In progress
**Roadmap ref:** `PROJECT_PLAN.md` → Implementation Phases, Days 6–8

---

> **Completed sprints**
> - Phase 0 (Days 1–2): Docker stack, config, safety — ✅ done
> - Phase 1 (Days 3–5): Mock API endpoints, pyproject.toml, CI — ✅ done

---

## Deliverables

### Notion workspace documentation
- [x] `notion/schema.md` — 7-DB schema with correct Relation fields (not Select)
- [x] Plants DB documented as the spine (DB 1 — created first)
- [x] Workflow Runs / Audit Log documented (DB 7)
- [x] Dedup key for every database listed
- [x] Creation order, share steps, and DB ID instructions documented
- [ ] 7 DBs **manually created** in Notion UI by user
- [ ] Integration token added to n8n Credentials
- [ ] All 7 DB IDs added to local `.env`

### n8n workflows
- [x] `n8n/workflows/w-reg.json` — Plant Registry Sync (importable)
- [x] `n8n/workflows/w2-asset-sync.json` — Asset Registry Sync (importable)
- [ ] Both workflows **imported** in running n8n and manually tested
- [ ] Audit log row visible in Workflow Runs / Audit Log DB after each run

### .env.example
- [ ] Add `NOTION_AUDIT_LOG_DB_ID` placeholder (currently missing)

---

## Validation Gate

```bash
# 1. Validate workflow JSON files are importable (basic JSON syntax)
python3 -c "import json; json.load(open('n8n/workflows/w-reg.json'))" && echo "w-reg OK"
python3 -c "import json; json.load(open('n8n/workflows/w2-asset-sync.json'))" && echo "w2 OK"
# Expected: "w-reg OK" and "w2 OK"

# 2. Import W-Reg in n8n UI
# n8n → Workflows → Import from file → select n8n/workflows/w-reg.json
# Expected: workflow appears with 11 nodes, no broken connections

# 3. Run W-Reg manually with test data
# n8n → W-Reg → Execute → Run manually
# Expected: Notion Plants DB gains 1 row for plant-001

# 4. Re-run W-Reg (idempotency check)
# Expected: 0 new rows created; existing row updated; no duplicate plant-001

# 5. Import and run W2 after W-Reg
# Expected: Assets DB gains 12 rows (12 devices for plant-001)

# 6. Check Audit Log DB
# Expected: 1 row per workflow run with Status = "✅ Success"

# 7. Check Plant relation in Assets
# Each asset in Assets DB should show a linked page in the Plant field
# Expected: clicking the relation opens the plant-001 page in Plants DB
```

**Most likely failure:** Notion node can't find the database.
**Fix:** In n8n, open each Notion node and re-select the Database ID field — paste the ID from `.env`. The `$env.NOTION_PLANTS_DB_ID` expression requires the env var to be set in n8n Settings → Environment Variables.

**Second most likely failure:** Relation field not accepted by Notion node.
**Fix:** The Plant relation field requires the **page ID** of the linked Plants record (a UUID), not the plant name or plant_id text. W2 fetches this page ID in the "Notion: Get plant page ID" step before creating assets.

---

## Next Sprint

**Phase 3 — W1 Daily KPI Sync + expected vs actual energy (Days 9–12)**

- Mock `/v1/plants/{id}/kpis?date=YYYY-MM-DD` endpoint
- W1 workflow: fetch KPI → compute expected energy → upsert Daily Performance DB
- Underperformance flag logic (variance % < −5)
- TimescaleDB `plant_kpis` insert from n8n
- Grafana datasource provisioned as code
