"""Storage-free HTTP liveness for the local development environment."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from app.api import router
from app.db import DatabaseUnavailable, dispose_engines


class HealthResponse(BaseModel):
    """HTTP liveness only, without assertions about external services."""

    status: Literal["ok"]


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        dispose_engines()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def invalid_input(request: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse({"detail": "Revisá los datos ingresados."}, status_code=422,
                        headers={"Cache-Control": "no-store"})


@app.exception_handler(HTTPException)
async def http_error(request: Request, error: HTTPException) -> JSONResponse:
    return JSONResponse({"detail": error.detail}, status_code=error.status_code,
                        headers={"Cache-Control": "no-store"})


@app.exception_handler(StaleDataError)
async def conflict(request: Request, error: StaleDataError) -> JSONResponse:
    return JSONResponse({"detail": "El registro fue modificado; actualizá antes de reintentar."},
                        status_code=409, headers={"Cache-Control": "no-store"})


@app.exception_handler(DatabaseUnavailable)
@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse({"detail": "El servicio no está disponible temporalmente."},
                        status_code=503, headers={"Cache-Control": "no-store"})


@app.get("/health", response_model=HealthResponse, status_code=200)
async def health() -> HealthResponse:
    """Return public technical liveness without configuration or external I/O."""
    return HealthResponse(status="ok")
