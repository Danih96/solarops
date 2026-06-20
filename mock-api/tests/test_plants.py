from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_get_plants_returns_list():
    r = client.get("/v1/plants")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_plants_count_matches_data():
    r = client.get("/v1/plants")
    assert len(r.json()) == 1


def test_get_devices_for_plant_001():
    r = client.get("/v1/plants/plant-001/devices")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_get_devices_returns_correct_plant_id():
    r = client.get("/v1/plants/plant-001/devices")
    for device in r.json():
        assert device["plant_id"] == "plant-001"


def test_get_devices_unknown_plant_returns_404():
    r = client.get("/v1/plants/nonexistent/devices")
    assert r.status_code == 404


def test_plant_schema_has_required_fields():
    r = client.get("/v1/plants")
    plant = r.json()[0]
    for field in ("plant_id", "name", "installed_capacity_kwp", "timezone", "status"):
        assert field in plant
