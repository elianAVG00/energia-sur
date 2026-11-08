"""Focused CU09 HTTP adapters; ownership before data access, domain rules reused."""

import os
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import diary, management
from app.db import get_engine
from app.models import Account, Domicile, Interruption, Meter, WebSession
from app.pdf import render_pdf
from app.schemas import (
    AccountOut,
    CloseInput,
    Correction,
    CutInput,
    CutOut,
    DomicileCorrection,
    DomicileInput,
    DomicileManagement,
    DomicileOut,
    Login,
    MeterCorrection,
    MeterInput,
    MeterOut,
    SessionOut,
    SummaryOut,
    parse_datetime,
)
from app.security import (
    COOKIE_NAME,
    DUMMY_HASH,
    SESSION_SECONDS,
    matches_csrf,
    new_token,
    token_hash,
    verify_password,
)


def no_cache(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(dependencies=[Depends(no_cache)])


def now() -> datetime:
    return datetime.now(UTC)


def database() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


DB = Annotated[Session, Depends(database)]


@dataclass(frozen=True)
class Actor:
    account: Account
    session: WebSession


def current(request: Request, db: DB) -> Actor:
    raw = request.cookies.get(COOKIE_NAME, "")
    session = db.get(WebSession, token_hash(raw)) if raw else None
    if session is None or session.revoked or session.expires_at <= now():
        raise HTTPException(401, "La sesión no es válida. Ingresá nuevamente.")
    account = db.get(Account, session.account_id)
    if account is None:
        raise HTTPException(401, "La sesión no es válida. Ingresá nuevamente.")
    return Actor(account, session)


Auth = Annotated[Actor, Depends(current)]


def origin(request: Request) -> None:
    allowed = os.environ.get(
        "APP_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if request.headers.get("origin", "") not in [x.strip() for x in allowed if x.strip()]:
        raise HTTPException(403, "El origen de la solicitud no está autorizado.")


def mutation(request: Request, actor: Auth) -> Actor:
    origin(request)
    if not matches_csrf(request.headers.get("x-csrf-token", ""), actor.session.csrf_token):
        raise HTTPException(403, "La solicitud no tiene un token CSRF válido.")
    return actor


Writer = Annotated[Actor, Depends(mutation)]


def session_out(actor: Actor) -> SessionOut:
    return SessionOut(
        account=AccountOut(id=actor.account.id, username=actor.account.username),
        csrf_token=actor.session.csrf_token,
    )


def own_domicile(db: Session, actor: Actor, domicile_id: str) -> Domicile:
    domicile = db.scalar(select(Domicile).where(
        Domicile.id == domicile_id, Domicile.account_id == actor.account.id,
    ))
    if domicile is None:
        raise HTTPException(404, "El recurso no está disponible.")
    return domicile


def own_cut(db: Session, actor: Actor, cut_id: str) -> Interruption:
    cut = db.scalar(select(Interruption).join(Domicile).where(
        Interruption.id == cut_id, Domicile.account_id == actor.account.id,
    ))
    if cut is None:
        raise HTTPException(404, "El recurso no está disponible.")
    return cut


def domicile_out(domicile: Domicile) -> DomicileOut:
    return DomicileOut(id=domicile.id, display_address=domicile.display_address)


def domain(cut: Interruption) -> diary.Interruption:
    return diary.Interruption(
        id=cut.id, domicile_id=cut.domicile_id, start_at=cut.start_at,
        end_at=cut.end_at, observations=cut.observations, complaint_number=cut.complaint_number,
    )


def cut_out(cut: Interruption) -> CutOut:
    value = domain(cut)
    return CutOut(
        id=cut.id, domicile_id=cut.domicile_id, start_at=value.start_at,
        end_at=value.end_at, observations=cut.observations,
        complaint_number=cut.complaint_number, version=cut.version, status=value.status,
    )


def validate(payload: CutInput, domicile_id: str) -> None:
    try:
        diary.validate_for_save(diary.Interruption(
            id="new", domicile_id=domicile_id, start_at=payload.start_at,
            end_at=payload.end_at,
        ), now=now())
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


def check_version(cut: Interruption, version: int) -> None:
    if cut.version != version:
        raise HTTPException(409, "El registro fue modificado; actualizá antes de reintentar.")


@router.post("/login", response_model=SessionOut)
def login(payload: Login, request: Request, response: Response, db: DB) -> SessionOut:
    origin(request)
    account = db.scalar(select(Account).where(Account.username == payload.username))
    valid = verify_password(payload.password, account.password_hash if account else DUMMY_HASH)
    if not valid or account is None:
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    raw_old = request.cookies.get(COOKIE_NAME, "")
    old = db.get(WebSession, token_hash(raw_old)) if raw_old else None
    if old is not None:
        old.revoked = True
    raw, csrf = new_token(), new_token()
    session = WebSession(
        token_hash=token_hash(raw), account_id=account.id, csrf_token=csrf,
        expires_at=now() + timedelta(seconds=SESSION_SECONDS), revoked=False,
    )
    db.add(session)
    db.commit()
    secure = os.environ.get("SESSION_COOKIE_SECURE") == "true" or request.headers.get(
        "origin", "",
    ).startswith("https://")
    response.set_cookie(
        COOKIE_NAME, raw, max_age=SESSION_SECONDS, httponly=True,
        samesite="lax", secure=secure, path="/",
    )
    return session_out(Actor(account, session))


@router.get("/session", response_model=SessionOut)
def session_info(actor: Auth) -> SessionOut:
    return session_out(actor)


@router.post("/logout", status_code=204)
def logout(response: Response, actor: Writer, db: DB) -> Response:
    actor.session.revoked = True
    db.commit()
    response.status_code = 204
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax")
    return response


@router.get("/domiciles", response_model=list[DomicileOut])
def domiciles(actor: Auth, db: DB) -> list[DomicileOut]:
    return [domicile_out(row) for row in db.scalars(select(Domicile).where(
        Domicile.account_id == actor.account.id,
    ).order_by(Domicile.display_address, Domicile.id))]


@router.post("/domiciles", status_code=201, response_model=DomicileOut)
def create_domicile(payload: DomicileInput, actor: Writer, db: DB) -> DomicileOut:
    domicile = Domicile(account_id=actor.account.id, display_address=payload.display_address)
    db.add(domicile)
    db.commit()
    return domicile_out(domicile)


def management_out(row: Domicile) -> DomicileManagement:
    return DomicileManagement(id=row.id, display_address=row.display_address, version=row.version)


def meter_out(row: Meter) -> MeterOut:
    return MeterOut(id=row.id, domicile_id=row.domicile_id, meter_number=row.meter_number,
                    alias=row.alias, version=row.version)


@router.get("/domiciles/{domicile_id}/management", response_model=DomicileManagement)
def get_management(domicile_id: str, actor: Auth, db: DB) -> DomicileManagement:
    return management_out(management.domicile(db, actor.account.id, domicile_id))


@router.patch("/domiciles/{domicile_id}", response_model=DomicileManagement)
def patch_domicile(
    domicile_id: str, payload: DomicileCorrection, actor: Writer, db: DB,
) -> DomicileManagement:
    return management_out(management.correct_domicile(
        db, actor.account.id, domicile_id, payload.display_address, payload.version,
    ))


@router.get("/domiciles/{domicile_id}/meters", response_model=list[MeterOut])
def list_meters(domicile_id: str, actor: Auth, db: DB) -> list[MeterOut]:
    return [meter_out(row) for row in management.meters(db, actor.account.id, domicile_id)]


@router.post("/domiciles/{domicile_id}/meters", status_code=201, response_model=MeterOut)
def add_meter(domicile_id: str, payload: MeterInput, actor: Writer, db: DB) -> MeterOut:
    return meter_out(management.create_meter(
        db, actor.account.id, domicile_id, payload.meter_number, payload.alias,
    ))


@router.get("/domiciles/{domicile_id}/meters/{meter_id}", response_model=MeterOut)
def get_meter(domicile_id: str, meter_id: str, actor: Auth, db: DB) -> MeterOut:
    return meter_out(management.meter(db, actor.account.id, domicile_id, meter_id))


@router.patch("/domiciles/{domicile_id}/meters/{meter_id}", response_model=MeterOut)
def patch_meter(
    domicile_id: str, meter_id: str, payload: MeterCorrection, actor: Writer, db: DB,
) -> MeterOut:
    return meter_out(management.correct_meter(
        db, actor.account.id, domicile_id, meter_id, payload.meter_number,
        payload.alias, payload.version,
    ))


def stored_cuts(db: Session, domicile_id: str) -> list[Interruption]:
    return list(db.scalars(select(Interruption).where(
        Interruption.domicile_id == domicile_id,
    ).order_by(Interruption.start_at.desc(), Interruption.id)))


@router.get("/domiciles/{domicile_id}/interruptions", response_model=list[CutOut])
def cuts(domicile_id: str, actor: Auth, db: DB) -> list[CutOut]:
    own_domicile(db, actor, domicile_id)
    return [cut_out(cut) for cut in stored_cuts(db, domicile_id)]


@router.post("/domiciles/{domicile_id}/interruptions", status_code=201, response_model=CutOut)
def create_cut(domicile_id: str, payload: CutInput, actor: Writer, db: DB) -> CutOut:
    own_domicile(db, actor, domicile_id)
    validate(payload, domicile_id)
    cut = Interruption(domicile_id=domicile_id, **payload.model_dump())
    db.add(cut)
    db.commit()
    return cut_out(cut)


@router.patch("/interruptions/{cut_id}", response_model=CutOut)
def correct_cut(cut_id: str, payload: Correction, actor: Writer, db: DB) -> CutOut:
    cut = own_cut(db, actor, cut_id)
    check_version(cut, payload.version)
    if cut.end_at is not None and payload.end_at is None:
        raise HTTPException(422, "No se puede reabrir un corte cerrado.")
    validate(payload, cut.domicile_id)
    cut.start_at, cut.end_at = payload.start_at, payload.end_at
    cut.observations, cut.complaint_number = payload.observations, payload.complaint_number
    db.commit()
    return cut_out(cut)


@router.post("/interruptions/{cut_id}/close", response_model=CutOut)
def close_cut(cut_id: str, payload: CloseInput, actor: Writer, db: DB) -> CutOut:
    cut = own_cut(db, actor, cut_id)
    check_version(cut, payload.version)
    if cut.end_at is not None:
        raise HTTPException(422, "El corte ya está cerrado.")
    validate(CutInput(start_at=cut.start_at, end_at=payload.end_at), cut.domicile_id)
    cut.end_at = payload.end_at
    db.commit()
    return cut_out(cut)


def report_data(
    domicile_id: str, period_start: str, period_end: str, actor: Actor, db: Session,
) -> tuple[Domicile, list[Interruption], diary.DiaryReport]:
    domicile = own_domicile(db, actor, domicile_id)
    records = stored_cuts(db, domicile_id)
    try:
        report = diary.generate_report(
            domicile_id=domicile_id, interruptions=[domain(cut) for cut in records],
            period=diary.ReportPeriod(parse_datetime(period_start), parse_datetime(period_end)),
            clock=now,
        )
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    return domicile, records, report


@router.get("/domiciles/{domicile_id}/summary", response_model=SummaryOut)
def summary(
    domicile_id: str, period_start: str, period_end: str, actor: Auth, db: DB,
) -> SummaryOut:
    domicile, records, report = report_data(domicile_id, period_start, period_end, actor, db)
    by_id = {cut.id: cut for cut in records}
    return SummaryOut(
        domicile=domicile_out(domicile), period_start=report.period.start_at,
        period_end=report.period.end_at, generated_at=report.generated_at,
        total_minutes=report.total_minutes, total_hours=report.hours,
        remaining_minutes=report.minutes,
        entries=[cut_out(by_id[row.interruption.id]) for row in report.rows],
    )


@router.get("/domiciles/{domicile_id}/report.pdf")
def pdf_report(
    domicile_id: str, period_start: str, period_end: str, actor: Auth, db: DB,
) -> Response:
    domicile, _, report = report_data(domicile_id, period_start, period_end, actor, db)
    try:
        content = render_pdf(domicile.display_address, report)
    except Exception:
        raise HTTPException(503, "No se pudo generar el PDF.") from None
    return Response(content, media_type="application/pdf", headers={
        "Content-Disposition": 'attachment; filename="interruption-diary.pdf"',
        "Cache-Control": "no-store",
    })
