"""Additive account-owned CU09 persistence, without implicit table creation."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def identifier() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "es_accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))


class WebSession(Base):
    __tablename__ = "es_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("es_accounts.id"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Domicile(Base):
    __tablename__ = "es_domiciles"
    __table_args__ = (
        UniqueConstraint("id", "account_id", name="uq_domicile_id_account"),
        CheckConstraint("version > 0", name="ck_domicile_version"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    account_id: Mapped[str] = mapped_column(ForeignKey("es_accounts.id"), index=True)
    display_address: Mapped[str] = mapped_column(String(300))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")


class Meter(Base):
    __tablename__ = "es_meters"
    __table_args__ = (
        UniqueConstraint("id", "account_id", name="uq_meter_id_account"),
        ForeignKeyConstraint(
            ["domicile_id", "account_id"], ["es_domiciles.id", "es_domiciles.account_id"],
            name="fk_meter_domicile_owner",
        ),
        CheckConstraint("version > 0", name="ck_meter_version"),
        CheckConstraint(
            "meter_number <> '' AND meter_number = btrim(meter_number, ' ') "
            "AND meter_number COLLATE \"C\" !~ '[^ -~]'",
            name="ck_meter_number_ascii",
        ),
        Index(
            "uq_meter_account_normalized", "account_id",
            text("(translate(btrim(meter_number, ' '), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                 "'abcdefghijklmnopqrstuvwxyz') COLLATE \"C\")"), unique=True,
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    domicile_id: Mapped[str] = mapped_column(String(36), nullable=False)
    account_id: Mapped[str] = mapped_column(String(36), nullable=False)
    meter_number: Mapped[str] = mapped_column(String(120), nullable=False)
    alias: Mapped[str | None] = mapped_column(String(120), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")


class Interruption(Base):
    __tablename__ = "es_interruptions"
    __table_args__ = (
        CheckConstraint("end_at IS NULL OR end_at > start_at", name="es_cut_positive"),
        CheckConstraint("version > 0", name="es_cut_version"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    domicile_id: Mapped[str] = mapped_column(ForeignKey("es_domiciles.id"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    complaint_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    __mapper_args__ = {"version_id_col": version}


class MeterReading(Base):
    """A confirmed reading; authorization is enforced through its meter."""

    __tablename__ = "es_meter_readings"
    __table_args__ = (
        UniqueConstraint("meter_id", "recorded_at", name="uq_reading_meter_instant"),
        UniqueConstraint("id", "meter_id", name="uq_reading_id_meter"),
        CheckConstraint("value_kwh >= 0 AND value_kwh = trunc(value_kwh) "
                        "AND value_kwh NOT IN ('NaN'::numeric, 'Infinity'::numeric, "
                        "'-Infinity'::numeric)",
                        name="ck_reading_value"),
        CheckConstraint("version > 0", name="ck_reading_version"),
        CheckConstraint("isfinite(recorded_at) AND date_trunc('second', recorded_at) = recorded_at",
                        name="ck_reading_second"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    meter_id: Mapped[str] = mapped_column(ForeignKey("es_meters.id"), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value_kwh: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    photo_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    photo_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")


class ReadingCreation(Base):
    """Committed response and fingerprint for an account/meter creation attempt."""

    __tablename__ = "es_reading_creations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["meter_id", "account_id"], ["es_meters.id", "es_meters.account_id"],
            name="fk_reading_creation_meter_owner",
        ),
        ForeignKeyConstraint(
            ["reading_id", "meter_id"], ["es_meter_readings.id", "es_meter_readings.meter_id"],
            name="fk_reading_creation_reading_meter",
        ),
    )
    account_id: Mapped[str] = mapped_column(ForeignKey("es_accounts.id"), primary_key=True)
    meter_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(36), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    reading_id: Mapped[str] = mapped_column(String(36), nullable=False)
    response: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ElectricityBill(Base):
    """A private bill associated with one stable meter."""

    __tablename__ = "es_electricity_bills"
    __table_args__ = (
        UniqueConstraint("meter_id", "period_start", "period_end", name="uq_bill_meter_period"),
        UniqueConstraint("id", "meter_id", name="uq_bill_id_meter"),
        CheckConstraint("isfinite(period_start) AND isfinite(period_end) AND period_start <= period_end",
                        name="ck_bill_period"),
        CheckConstraint("value_kwh >= 0 AND value_kwh < 1000000000000000000 "
                        "AND value_kwh = trunc(value_kwh, 3)", name="ck_bill_kwh"),
        CheckConstraint("amount_ars IS NULL OR (amount_ars >= 0 AND "
                        "amount_ars < 1000000000000000000 AND amount_ars = trunc(amount_ars, 2))",
                        name="ck_bill_amount"),
        CheckConstraint("version > 0", name="ck_bill_version"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    meter_id: Mapped[str] = mapped_column(ForeignKey("es_meters.id"), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    value_kwh: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    amount_ars: Mapped[Decimal | None] = mapped_column(Numeric(), nullable=True)
    file_key: Mapped[str] = mapped_column(String(64), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")


class BillCreation(Base):
    """Committed create response for an account and meter's idempotency key."""
    __tablename__ = "es_bill_creations"
    __table_args__ = (
        ForeignKeyConstraint(["meter_id", "account_id"], ["es_meters.id", "es_meters.account_id"],
                             name="fk_bill_creation_meter_owner"),
        ForeignKeyConstraint(["bill_id", "meter_id"],
                             ["es_electricity_bills.id", "es_electricity_bills.meter_id"],
                             name="fk_bill_creation_bill_meter"),
    )
    account_id: Mapped[str] = mapped_column(ForeignKey("es_accounts.id"), primary_key=True)
    meter_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(36), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    bill_id: Mapped[str] = mapped_column(String(36), nullable=False)
    response: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class OutageSnapshot(Base):
    """One acquired ENRE snapshot; exactly one row is the current state."""

    __tablename__ = "es_outage_snapshots"
    __table_args__ = (
        CheckConstraint("total_users_without IS NULL OR total_users_without >= 0",
                        name="ck_outage_total_without"),
        CheckConstraint("total_users_with IS NULL OR total_users_with >= 0",
                        name="ck_outage_total_with"),
        CheckConstraint("users_affected_yesterday IS NULL OR users_affected_yesterday >= 0",
                        name="ck_outage_total_yesterday"),
        Index("uq_outage_snapshot_current", "is_current", unique=True,
              postgresql_where=text("is_current")),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    distributor: Mapped[str] = mapped_column(String(32), nullable=False)
    source_url: Mapped[str] = mapped_column(String(300), nullable=False)
    source_last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    source_reported_time: Mapped[str | None] = mapped_column(String(16), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"),
    )
    total_users_without: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_users_with: Mapped[int | None] = mapped_column(Integer, nullable=True)
    users_affected_yesterday: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_counts: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class OutageReport(Base):
    """One normalized outage row belonging to a snapshot."""

    __tablename__ = "es_outage_reports"
    __table_args__ = (
        CheckConstraint("affected_users IS NULL OR affected_users >= 0",
                        name="ck_outage_report_users"),
        CheckConstraint("category IN ('medium_voltage','low_voltage','preventive')",
                        name="ck_outage_report_category"),
        Index("ix_outage_report_snapshot", "snapshot_id"),
        Index("ix_outage_report_area", "partido_key", "localidad_key"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("es_outage_snapshots.id", ondelete="CASCADE"), nullable=False,
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    partido: Mapped[str] = mapped_column(String(120), nullable=False)
    localidad: Mapped[str | None] = mapped_column(String(120), nullable=True)
    partido_key: Mapped[str] = mapped_column(String(120), nullable=False)
    localidad_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    subestacion_alimentador: Mapped[str | None] = mapped_column(String(200), nullable=True)
    affected_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    normalizacion: Mapped[str | None] = mapped_column(String(120), nullable=True)


class OutageFetchRun(Base):
    """Every acquisition attempt, including failures and skipped runs."""

    __tablename__ = "es_outage_fetch_runs"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('ok','not_modified','http_error','tls_error','parse_error',"
            "'schema_error','source_degraded','timeout','skipped_locked')",
            name="ck_outage_run_outcome",
        ),
        Index("ix_outage_run_started", "started_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
