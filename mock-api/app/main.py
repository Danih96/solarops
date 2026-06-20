from __future__ import annotations

from fastapi import FastAPI

from app.routers import plants

app = FastAPI(title="SynaptiQ Mock API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "solarops-mock-api"}


app.include_router(plants.router)
