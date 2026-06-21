# Notion Workspace Schema — SolarOps

> **Rule:** `Plant` is a **Relation → Plants** in every database. Never use a free-text Select for plant references.
>
> **Dedup strategy:** Each database has an explicit dedup key. n8n queries this field before create/update.

---

## Step 1 — Create Notion Integration

1. Go to `https://www.notion.so/my-integrations`
2. Click **New Integration**
3. Name: `solarops-n8n`
4. Capabilities: **Content read + write** only (no Comments, no User info)
5. Copy the **Internal Integration Token** (`secret_xxx`)
6. In n8n: Settings → Credentials → New → Notion API → paste token

---

## Step 2 — Create Workspace Structure

Create a top-level page called **SolarOps** in Notion.
Under it, create the following **7 full-page databases** in order (Plants first — all others Relate to it).

---

### DB 1 — Plants

*The spine. Every other database relates to a page in Plants.*

| Property | Type | Notes |
|---|---|---|
| Plant Name | Title | e.g. "Parc Fotovoltaic Ilfov" |
| Plant ID | Text | join key with API (`plant-001`); **dedup key for W-Reg** |
| Owner | Text | e.g. "SolarCo SRL" |
| Location | Text | e.g. "Ilfov, Romania" |
| Country | Select | Romania, Bulgaria, Greece, … |
| Timezone | Select | Europe/Bucharest, Europe/Sofia, … |
| Installed Capacity kWp | Number | e.g. 530 |
| SLA Tier | Select | Bronze, Silver, Gold |
| O&M Provider | Text | e.g. "SolarOps Demo" |
| Status | Select | Active, Commissioning, Decommissioned |
| Go-live Date | Date | |

---

### DB 2 — Assets

| Property | Type | Notes |
|---|---|---|
| Name | Title | e.g. "Inverter INV-01" |
| SynaptiQ Device ID | Text | `device_id` from API; **dedup key for W2** |
| Plant | **Relation → Plants** | link to DB 1 |
| Asset Type | Select | Inverter, Meter, Sensor, BMS, Gateway |
| Vendor | Select | Huawei, Fronius, SMA, ABB, Other |
| Rated Power kWp | Number | |
| Serial Number | Text | |
| Status | Select | Active, Offline, Maintenance |
| Installed Date | Date | |
| Last Seen | Date | updated by W2 on each sync |

---

### DB 3 — Daily Performance

| Property | Type | Notes |
|---|---|---|
| Name | Title | auto-generated: `{plant_id}_{date}` |
| Plant | **Relation → Plants** | link to DB 1 |
| Date | Date | |
| Actual Energy kWh | Number | from API |
| Irradiance kWh/m² | Number | from API |
| Availability % | Number | from API |
| PR % | Number | from API |
| Expected Energy kWh | Number | computed by n8n: `capacity × irradiance × 0.80` |
| Variance kWh | Number | computed by n8n: `actual − expected` |
| Variance % | Number | computed by n8n: `variance / expected × 100` |
| Estimated Revenue Loss | Number | computed by n8n: `abs(variance) × tariff` |
| Underperformance Flag | Checkbox | set by n8n when `variance % < −5` |
| Underperformance Reason | Select | Low Irradiance, Low PR, Comms Loss, Unknown |
| Status | Select | ✅ OK, ⚠️ Low PR, 🔴 Critical |

> **Dedup key for W1:** `{plant_id}_{date}` stored in Name field.

---

### DB 4 — Service Tickets

| Property | Type | Notes |
|---|---|---|
| Name | Title | e.g. "CRIT-INV-01-2024-01-15" |
| Alarm ID | Text | **dedup key for W3**; from API |
| Plant | **Relation → Plants** | link to DB 1 |
| Asset | Relation → Assets | link to DB 2 |
| Severity | Select | Critical, High, Medium, Low |
| kWp Affected | Number | |
| Alarm Type | Select | Inverter Offline, Low PR, Comm Loss, Overtemp, Grid Fault |
| Detected At | Date | |
| Acknowledged At | Date | |
| Resolved At | Date | |
| Status | Select | Open, Acknowledged, In Progress, Resolved |
| Root Cause | Text | |
| Action Taken | Text | |

---

### DB 5 — PM Tickets

*Schema defined now. Workflow created in a later sprint.*

| Property | Type | Notes |
|---|---|---|
| Name | Title | e.g. "Q1 2024 PM — Ilfov" |
| Plant | **Relation → Plants** | link to DB 1 |
| PM Type | Select | Quarterly, Annual, Ad-hoc |
| Scheduled Date | Date | |
| Status | Select | Planned, In Progress, Completed |
| Assets | Relation → Assets | multi-select relation |
| Inspection Points | Number | checklist items completed |

---

### DB 6 — Reports

*Schema defined now. Workflow created in a later sprint.*

| Property | Type | Notes |
|---|---|---|
| Name | Title | e.g. "Monthly Report Jan 2024 — Ilfov" |
| Plant | **Relation → Plants** | link to DB 1 |
| Period | Select | Monthly, Quarterly, Annual |
| Report Date | Date | |
| Status | Select | Draft, Generated, Delivered |
| PDF Link | URL | |
| Delivered To | Email | |

---

### DB 7 — Workflow Runs / Audit Log

*Every workflow writes one row here at the end of execution.*

| Property | Type | Notes |
|---|---|---|
| Run Name | Title | `{workflow}_{timestamp}` e.g. "W-Reg_2024-01-15T06:00" |
| Workflow Name | Select | W-Reg, W2, W1, W3, W-Err |
| Run ID | Text | n8n execution ID |
| Trigger Type | Select | Schedule, Manual, Error |
| Started At | Date | with time |
| Finished At | Date | with time |
| Status | Select | ✅ Success, ⚠️ Partial, ❌ Failed |
| Records Processed | Number | |
| Records Created | Number | |
| Records Updated | Number | |
| Records Skipped | Number | |
| Error Message | Text | populated by W-Err on failure |
| Source Endpoint | Text | e.g. `/v1/plants` |
| Target System | Select | Notion, TimescaleDB, Both |
| Plant | Relation → Plants | optional; used when workflow is plant-scoped |

> **No dedup key.** Each workflow run creates a new row. Run ID prevents duplicate audit entries.

---

## Step 3 — Share Each Database with the Integration

For **each of the 7 databases**:
1. Open the database full-page
2. Click **Share** (top right)
3. Click **Invite** → select `solarops-n8n`
4. Set permission: **Can edit**

---

## Step 4 — Copy Database IDs and Add to `.env`

Each database URL:
```
https://www.notion.so/your-workspace/DATABASE_ID?v=...
```

Copy each `DATABASE_ID` and add to your local `.env`:

```
NOTION_TOKEN=secret_xxx
NOTION_PLANTS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_ASSETS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DAILY_PERF_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_TICKETS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PM_TICKETS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_REPORTS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_AUDIT_LOG_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

These IDs are used as the **Database ID** field in all n8n Notion nodes.

---

## Relation Order Matters

Create databases in this order to avoid broken relation targets:

1. **Plants** (no relations; spine)
2. **Assets** (relates to Plants)
3. **Daily Performance** (relates to Plants)
4. **Service Tickets** (relates to Plants + Assets)
5. **PM Tickets** (relates to Plants + Assets)
6. **Reports** (relates to Plants)
7. **Workflow Runs / Audit Log** (optional relation to Plants)

---

## Dedup Key Summary

| Database | Dedup Key | Workflow |
|---|---|---|
| Plants | `Plant ID` (Text) | W-Reg |
| Assets | `SynaptiQ Device ID` (Text) | W2 |
| Daily Performance | `Name` = `{plant_id}_{date}` | W1 |
| Service Tickets | `Alarm ID` (Text) | W3 |
| PM Tickets | — | manual |
| Reports | — | manual |
| Workflow Runs / Audit Log | `Run ID` (Text) | all workflows |
