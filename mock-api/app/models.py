from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Plant(BaseModel):
    plant_id: str
    name: str
    owner: str
    location: str
    country: str
    timezone: str
    installed_capacity_kwp: float
    sla_tier: str
    om_provider: str
    status: str
    go_live_date: str


class Device(BaseModel):
    device_id: str
    name: str
    asset_type: str
    plant_id: str
    vendor: str
    rated_power_kwp: Optional[float]
    serial_number: str
    status: str
    installed_date: str
    latitude: float
    longitude: float
