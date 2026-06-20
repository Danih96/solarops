# Notion Workspace Setup

## Step 1 — Create Integration

1. Go to `https://www.notion.so/my-integrations`
2. Click **New Integration**
3. Name: `solarops-n8n`
4. Capabilities: Content (read + write) + Comments (none)
5. Copy the **Internal Integration Token** (`secret_xxx`)
6. Add to n8n: Settings → Credentials → New → Notion API → paste token

## Step 2 — Create Workspace Structure

Create a top-level page called **SolarOps** in Notion. Under it, create 5 full-page databases:

### 1. Assets
Properties:
- Name (Title)
- Asset Type (Select): Inverter, Meter, Sensor, BMS, Gateway
- Plant (Select): add plant names as options
- Vendor (Select): Huawei, Fronius, SMA, ABB, other
- Rated Power kWp (Number)
- Serial Number (Text)
- SynaptiQ Device ID (Text) ← join key with API
- Status (Select): Active, Offline, Maintenance
- Installed Date (Date)
- Last Seen (Date)

### 2. Daily Performance
Properties:
- Name (Title)
- Plant (Select)
- Date (Date)
- Energy Yield kWh (Number)
- Performance Ratio % (Number)
- Irradiance kWh/m2 (Number)
- Availability % (Number)
- Specific Yield kWh/kWp (Number)
- Status (Select): ✅ OK, ⚠️ Low PR, 🔴 Critical

### 3. Service Tickets
Properties:
- Name (Title)
- Alarm ID (Text) ← deduplication key
- Asset (Relation → Assets)
- Plant (Select)
- Severity (Select): Critical, High, Medium, Low
- kWp Affected (Number)
- Alarm Type (Select): Inverter Offline, Low PR, Comm Loss, Overtemp, Grid Fault
- Detected At (Date)
- Acknowledged At (Date)
- Resolved At (Date)
- Status (Select): Open, Acknowledged, In Progress, Resolved
- Root Cause (Text)
- Action Taken (Text)

### 4. PM Tickets
Properties:
- Name (Title)
- Plant (Select)
- PM Type (Select): Quarterly, Annual, Ad-hoc
- Scheduled Date (Date)
- Status (Select): Planned, In Progress, Completed
- Assets (Relation → Assets)
- Inspection Points (Number)
- Assigned To (Person)

### 5. Reports
Properties:
- Name (Title)
- Plant (Select)
- Period (Select): Monthly, Quarterly, Annual
- Report Date (Date)
- Status (Select): Draft, Generated, Delivered
- PDF Link (URL)
- Delivered To (Email)

## Step 3 — Share Databases with Integration

For each of the 5 databases:
1. Open the database full-page
2. Click **Share** (top right)
3. Click **Invite** → select `solarops-n8n`
4. Set permission: **Can edit**

## Step 4 — Copy Database IDs

Each database URL looks like:
`https://www.notion.so/your-workspace/DATABASE_ID?v=...`

Copy each DATABASE_ID and add to `.env`:
```
NOTION_ASSETS_DB_ID=xxx
NOTION_DAILY_PERF_DB_ID=xxx
NOTION_TICKETS_DB_ID=xxx
NOTION_PM_TICKETS_DB_ID=xxx
NOTION_REPORTS_DB_ID=xxx
```

These are used in n8n Notion nodes as the Database ID field.
