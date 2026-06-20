-- SolarOps TimescaleDB schema
-- n8n uses schema 'n8n' (created automatically by n8n on first start)
-- Plant KPI data lives in schema 'public'

CREATE TABLE IF NOT EXISTS plant_kpis (
    time                    TIMESTAMPTZ NOT NULL,
    plant_id                TEXT NOT NULL,
    plant_name              TEXT,
    energy_yield_kwh        DOUBLE PRECISION,
    performance_ratio       DOUBLE PRECISION,
    irradiance_kwh_m2       DOUBLE PRECISION,
    availability_percent    DOUBLE PRECISION,
    specific_yield_kwh_kwp  DOUBLE PRECISION
);

SELECT create_hypertable('plant_kpis', 'time', if_not_exists => TRUE);

-- Continuous aggregate: daily KPI rollup
CREATE MATERIALIZED VIEW IF NOT EXISTS plant_kpis_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    plant_id,
    AVG(performance_ratio)      AS avg_pr,
    SUM(energy_yield_kwh)       AS total_yield_kwh,
    AVG(availability_percent)   AS avg_availability
FROM plant_kpis
GROUP BY day, plant_id
WITH NO DATA;
