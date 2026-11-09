"""Additive account-owned CU09 persistence, without implicit table creation."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
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
