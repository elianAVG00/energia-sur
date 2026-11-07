"""Storage-free HTTP liveness for the local development environment."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """HTTP liveness only, without assertions about external services."""

    status: Literal["ok"]


app = FastAPI()


@app.get("/health", response_model=HealthResponse, status_code=200)
async def health() -> HealthResponse:
    """Return public technical liveness without configuration or external I/O."""
    return HealthResponse(status="ok")
