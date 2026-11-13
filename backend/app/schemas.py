"""Typed, extra-field rejecting transport schemas for the accepted CU09 contract."""

import re
import unicodedata
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.diary import BUENOS_AIRES


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Schema):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=1024)


class AccountOut(Schema):
    id: str
    username: str
    role: Literal["user", "admin"]


class SessionOut(Schema):
    account: AccountOut
    csrf_token: str


class DomicileInput(Schema):
    display_address: str = Field(min_length=1, max_length=300)

    @field_validator("display_address")
    @classmethod
    def nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A domicile address is required.")
        return value


class DomicileOut(Schema):
    id: str
    display_address: str


class DomicileCorrection(DomicileInput):
    version: int = Field(strict=True, gt=0)


class DomicileManagement(DomicileOut):
    version: int


class MeterInput(Schema):
    meter_number: str
    alias: str | None = None

    @field_validator("meter_number")
    @classmethod
    def valid_number(cls, value: str) -> str:
        if any(not 0x20 <= ord(char) <= 0x7e for char in value):
            raise ValueError("Meter number must contain printable ASCII only.")
        value = value.strip(" ")
        if not 1 <= len(value) <= 120:
            raise ValueError("Meter number must contain 1 to 120 characters.")
        return value

    @field_validator("alias")
    @classmethod
    def valid_alias(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if any(unicodedata.category(char) == "Cc" for char in value):
            raise ValueError("Alias must not contain control characters.")
        value = value.strip()
        if len(value) > 120:
            raise ValueError("Alias must contain at most 120 characters.")
        return value or None


class MeterCorrection(MeterInput):
    alias: str | None
    version: int = Field(strict=True, gt=0)


class MeterOut(Schema):
    id: str
    domicile_id: str
    meter_number: str
    alias: str | None
    version: int


def local_datetime(value: datetime) -> datetime:
    try:
        if value.tzinfo is None:
            value = value.replace(tzinfo=BUENOS_AIRES)
        return value.astimezone(BUENOS_AIRES)
    except (OverflowError, ValueError):
        raise ValueError("Invalid Buenos Aires datetime.") from None


def parse_datetime(value: object) -> datetime:
    # Python datetimes are permitted for internal adapters, never numeric JSON coercion.
    if isinstance(value, datetime):
        return local_datetime(value)
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::00)?(?:Z|[+-]\d{2}:\d{2})?", value,
    ) is None:
        raise ValueError("Use minute-resolution ISO dates.")
    try:
        return local_datetime(datetime.fromisoformat(value))
    except (OverflowError, ValueError):
        raise ValueError("Invalid Buenos Aires datetime.") from None


class CutInput(Schema):
    start_at: datetime
    end_at: datetime | None = None
    observations: str | None = Field(default=None, max_length=4000)
    complaint_number: str | None = Field(default=None, max_length=120)

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def dates(cls, value: object) -> datetime | None:
        return None if value is None else parse_datetime(value)


class Correction(CutInput):
    version: int = Field(strict=True, gt=0)


class CloseInput(Schema):
    end_at: datetime
    version: int = Field(strict=True, gt=0)

    @field_validator("end_at", mode="before")
    @classmethod
    def dates(cls, value: object) -> datetime:
        return parse_datetime(value)


class CutOut(Schema):
    id: str
    domicile_id: str
    start_at: datetime
    end_at: datetime | None
    observations: str | None
    complaint_number: str | None
    version: int
    status: Literal["ongoing", "closed"]


class SummaryOut(Schema):
    domicile: DomicileOut
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    timezone: Literal["America/Argentina/Buenos_Aires"] = "America/Argentina/Buenos_Aires"
    total_minutes: int
    total_hours: int
    remaining_minutes: int
    entries: list[CutOut]
