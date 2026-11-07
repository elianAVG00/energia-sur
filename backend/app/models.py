"""Additive account-owned CU09 persistence, without implicit table creation."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
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
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    account_id: Mapped[str] = mapped_column(ForeignKey("es_accounts.id"), index=True)
    display_address: Mapped[str] = mapped_column(String(300))


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
