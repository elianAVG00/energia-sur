"""Storage-free HTTP liveness for the local development environment."""

import asyncio
import logging
import os
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app import admin_api, management, outage_store, scheduled_store, source_config
from app.api import router
from app.assistant_api import router as assistant_router
from app.assistant_limits import max_body_bytes
from app.bill_api import router as bill_router
from app.bill_reconcile import reconcile_bills
from app.comparison_api import router as comparison_router
from app.consumption_api import router as consumption_router
from app.db import DatabaseUnavailable, dispose_engines
from app.guide_store import ingest_guide
from app.outages_api import router as outage_router
from app.photo_store import reconcile_photos
from app.reading_api import DuplicateReading
from app.reading_api import router as reading_router
from app.reading_store import IdempotencyKeyReused, ReadingVersionConflict
from app.scheduled_api import router as scheduled_router
from app.source_config import InvalidInterval, SourceBusy
from app.source_config import VersionConflict as SourceVersionConflict

_LOGGER = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """HTTP liveness only, without assertions about external services."""

    status: Literal["ok"]


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    scheduler: asyncio.Task[None] | None = None
    scheduled_scheduler: asyncio.Task[None] | None = None
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
        if os.environ.get("OUTAGE_SCHEDULER_ENABLED", "false").lower() in {
            "1", "true", "yes",
        }:
            scheduler = asyncio.create_task(_outage_scheduler())
        if os.environ.get("SCHEDULED_WORKS_SCHEDULER_ENABLED", "false").lower() in {
            "1", "true", "yes",
        }:
            scheduled_scheduler = asyncio.create_task(_scheduled_works_scheduler())
        if os.environ.get("ASSISTANT_GUIDE_INGEST", "false").lower() in {
            "1", "true", "yes",
        }:
            try:
                outcome = await run_in_threadpool(ingest_guide)
                _LOGGER.info("Guide ingest outcome: %s.", outcome.outcome)
            except Exception as error:
                # Never abort startup or other schedulers on a guide failure.
                _LOGGER.warning("Guide ingest failed (%s).", type(error).__name__)
        yield
    finally:
        for task in (scheduler, scheduled_scheduler):
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError, Exception):
                    await task
        dispose_engines()


async def _outage_scheduler() -> None:
    while True:
        interval = await run_cycle("outages", outage_store.refresh_once)
        # The interval is read again on the next cycle; a change is not instant.
        await asyncio.sleep(float(max(interval, 30)))


async def _scheduled_works_scheduler() -> None:
    while True:
        interval = await run_cycle(
            "scheduled_works", scheduled_store.refresh_once,
        )
        # The interval is read again on the next cycle; a change is not instant.
        await asyncio.sleep(float(max(interval, 30)))


async def run_cycle(source_key: str, refresh: Callable[[], str]) -> int:
    """Run one scheduler cycle and return the interval to sleep for."""
    interval = await run_in_threadpool(next_interval, source_key)
    try:
        await run_in_threadpool(refresh)
    except Exception as error:
        # No payload, URL or database detail is logged.
        _LOGGER.warning("%s refresh failed (%s).", source_key, type(error).__name__)
    return interval


def next_interval(source_key: str) -> int:
    """Read the persisted interval for one cycle, falling back safely."""
    try:
        return source_config.get_interval(source_key)
    except Exception as error:
        _LOGGER.warning("Source interval read failed (%s).", type(error).__name__)
        return source_config.DEFAULT_INTERVAL


class AssistantBodyLimitMiddleware:
    """Reject oversized assistant bodies before JSON parsing (pure ASGI)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not str(scope.get("path", "")).endswith(
            "/assistant/chat",
        ):
            await self.app(scope, receive, send)
            return
        limit = max_body_bytes()
        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length", b"")
        if length.isdigit() and int(length) > limit:
            await self._too_large(scope, receive, send)
            return
        body = bytearray()
        pending: Message | None = None
        while True:
            message = await receive()
            if message["type"] != "http.request":
                pending = message
                break
            chunk = message.get("body", b"")
            if isinstance(chunk, bytes):
                body.extend(chunk)
            if len(body) > limit:
                await self._too_large(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {
                    "type": "http.request", "body": bytes(body), "more_body": False,
                }
            if pending is not None:
                return pending
            return await receive()

        await self.app(scope, replay, send)

    @staticmethod
    async def _too_large(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            {"detail": "La solicitud es demasiado grande."},
            status_code=413,
            headers={"Cache-Control": "no-store"},
        )
        await response(scope, receive, send)


app = FastAPI(lifespan=lifespan)
app.add_middleware(AssistantBodyLimitMiddleware)
app.include_router(router)
app.include_router(reading_router)
app.include_router(bill_router)
app.include_router(comparison_router)
app.include_router(consumption_router)
app.include_router(outage_router)
app.include_router(scheduled_router)
app.include_router(admin_api.router)
app.include_router(assistant_router)


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


@app.exception_handler(SourceBusy)
async def source_busy(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(
        {"detail": "La fuente se está actualizando; esperá y reintentá.",
         "code": "SOURCE_BUSY"},
        status_code=409, headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(SourceVersionConflict)
async def source_version_conflict(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(
        {"detail": "La configuración fue modificada; recargá e intentá nuevamente.",
         "code": "VERSION_CONFLICT"},
        status_code=409, headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(InvalidInterval)
async def invalid_interval(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(
        {"detail": "El intervalo de actualización no está permitido."},
        status_code=422, headers={"Cache-Control": "no-store"},
    )


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
