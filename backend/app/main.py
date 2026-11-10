"""Storage-free HTTP liveness for the local development environment."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError
from starlette.concurrency import run_in_threadpool

from app import management
from app.api import router
from app.bill_api import router as bill_router
from app.bill_reconcile import reconcile_bills
from app.comparison_api import router as comparison_router
from app.consumption_api import router as consumption_router
from app.db import DatabaseUnavailable, dispose_engines
from app.photo_store import reconcile_photos
from app.reading_api import DuplicateReading
from app.reading_api import router as reading_router
from app.reading_store import IdempotencyKeyReused, ReadingVersionConflict

_LOGGER = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """HTTP liveness only, without assertions about external services."""

    status: Literal["ok"]


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    try:
        # Fail closed: if recovery cannot prove the locks, no files are removed.
        try:
            await run_in_threadpool(reconcile_photos)
        except Exception as error:
            # Log only the failure class: no paths, keys or user data.
            _LOGGER.warning("Photo reconciliation failed; no files were removed (%s).",
                            type(error).__name__)
        try:
            await run_in_threadpool(reconcile_bills)
        except Exception as error:
            _LOGGER.warning("Bill reconciliation failed; no files were removed (%s).",
                            type(error).__name__)
        yield
    finally:
        dispose_engines()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.include_router(reading_router)
app.include_router(bill_router)
app.include_router(comparison_router)
app.include_router(consumption_router)


@app.exception_handler(DuplicateReading)
@app.exception_handler(IdempotencyKeyReused)
@app.exception_handler(ReadingVersionConflict)
async def reading_conflict(request: Request, error: Exception) -> JSONResponse:
    if isinstance(error, DuplicateReading):
        code = "DUPLICATE_READING"
    elif isinstance(error, IdempotencyKeyReused):
        code = "IDEMPOTENCY_KEY_REUSED"
    else:
        code = "VERSION_CONFLICT"
    return JSONResponse({"detail": "El registro entra en conflicto con datos existentes.", "code": code},
                        status_code=409, headers={"Cache-Control": "no-store"})


@app.exception_handler(management.MissingResource)
async def missing_management(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse({"detail": "El recurso no está disponible."}, status_code=404,
                        headers={"Cache-Control": "no-store"})


@app.exception_handler(management.VersionConflict)
async def management_conflict(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse({"detail": "El registro fue modificado; actualizá antes de reintentar.",
                         "code": "VERSION_CONFLICT"}, status_code=409,
                        headers={"Cache-Control": "no-store"})


@app.exception_handler(management.DuplicateMeter)
async def duplicate_meter(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse({"detail": "Ya existe un medidor con ese número.",
                         "code": "DUPLICATE_METER"}, status_code=409,
                        headers={"Cache-Control": "no-store"})


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
