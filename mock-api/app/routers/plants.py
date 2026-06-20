from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models import Device, Plant

router = APIRouter(prefix="/v1/plants", tags=["plants"])

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_plants() -> list[dict]:
    with (_DATA_DIR / "plants.json").open() as fh:
        return json.load(fh)


def _load_devices() -> dict[str, list[dict]]:
    with (_DATA_DIR / "devices.json").open() as fh:
        return json.load(fh)


@router.get("", response_model=list[Plant])
def get_plants() -> list[Plant]:
    return _load_plants()


@router.get("/{plant_id}/devices", response_model=list[Device])
def get_devices(plant_id: str) -> list[Device]:
    devices = _load_devices()
    if plant_id not in devices:
        raise HTTPException(status_code=404, detail=f"Plant '{plant_id}' not found")
    return devices[plant_id]
