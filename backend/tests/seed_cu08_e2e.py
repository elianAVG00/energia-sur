"""Seed synthetic CU08 consumption scenarios for browser verification.

This is a verification helper, not a test module. It writes one synthetic
domicile/meter with readings per scenario for an existing account.
"""

import json
import os
import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.diary import BUENOS_AIRES
from app.models import Account, Domicile, Meter, MeterReading

SCENARIOS: dict[str, list[tuple[date, str]]] = {
    "main": [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1020"),
             (date(2026, 11, 7), "1080")],
    "decreasing": [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1080"),
                   (date(2026, 11, 7), "1020")],
    "zero": [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1000")],
    "isolation": [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1020")],
}


def instant(local: date) -> datetime:
    return datetime.combine(local, time(12), tzinfo=BUENOS_AIRES).astimezone(UTC)


def main() -> None:
    username = os.environ["CU08_SEED_USER"]
    suffix = uuid.uuid4().hex[:8]
    output: dict[str, object] = {}
    with Session(get_engine()) as db:
        account = db.scalar(select(Account).where(Account.username == username))
        if account is None:
            raise SystemExit("Seed account not found.")
        for name, readings in SCENARIOS.items():
            domicile = Domicile(account_id=account.id, display_address=f"CU08 {name}")
            db.add(domicile)
            db.flush()
            meter = Meter(domicile_id=domicile.id, account_id=account.id,
                          meter_number=f"CU08-{name}-{suffix}", alias=None)
            db.add(meter)
            db.flush()
            reading_ids: list[str] = []
            for local, value in readings:
                row = MeterReading(id=str(uuid.uuid4()), meter_id=meter.id,
                                   recorded_at=instant(local), value_kwh=Decimal(value),
                                   photo_key=None, photo_type=None, version=1)
                db.add(row)
                reading_ids.append(row.id)
            db.flush()
            output[name] = {"domicile": domicile.id, "meter": meter.id, "readings": reading_ids}
        db.commit()
    print(json.dumps(output))


if __name__ == "__main__":
    main()
