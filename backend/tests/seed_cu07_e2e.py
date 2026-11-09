"""Seed synthetic CU07 comparison scenarios for browser verification.

This is a verification helper, not a test module. It writes one synthetic
domicile/meter/bill with readings per scenario for an existing account.
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
from app.models import Account, Domicile, ElectricityBill, Meter, MeterReading

SCENARIOS: dict[str, tuple[list[tuple[date, str]], tuple[date, date]]] = {
    "exact": ([(date(2026, 10, 1), "1000"), (date(2026, 10, 31), "1120")],
              (date(2026, 10, 1), date(2026, 10, 31))),
    "multiple": ([(date(2026, 10, 1), "1000"), (date(2026, 10, 2), "1050"),
                  (date(2026, 10, 7), "1120")],
                 (date(2026, 10, 1), date(2026, 10, 7))),
    "approximate": ([(date(2026, 9, 24), "1000"), (date(2026, 10, 14), "1120")],
                    (date(2026, 10, 1), date(2026, 10, 7))),
    "zero": ([(date(2026, 10, 1), "1000"), (date(2026, 10, 31), "1000")],
             (date(2026, 10, 1), date(2026, 10, 31))),
    "decreasing": ([(date(2026, 9, 1), "1200"), (date(2026, 9, 30), "1100")],
                   (date(2026, 9, 1), date(2026, 9, 30))),
    "isolation": ([(date(2026, 10, 1), "1000"), (date(2026, 10, 31), "1120")],
                  (date(2026, 10, 1), date(2026, 10, 31))),
}


def instant(local: date) -> datetime:
    return datetime.combine(local, time(12), tzinfo=BUENOS_AIRES).astimezone(UTC)


def main() -> None:
    username = os.environ["CU07_SEED_USER"]
    suffix = uuid.uuid4().hex[:8]
    output: dict[str, object] = {}
    with Session(get_engine()) as db:
        account = db.scalar(select(Account).where(Account.username == username))
        if account is None:
            raise SystemExit("Seed account not found.")
        for name, (readings, period) in SCENARIOS.items():
            domicile = Domicile(account_id=account.id, display_address=f"CU07 {name}")
            db.add(domicile)
            db.flush()
            meter = Meter(domicile_id=domicile.id, account_id=account.id,
                          meter_number=f"CU07-{name}-{suffix}", alias=None)
            db.add(meter)
            db.flush()
            reading_ids: list[str] = []
            for local, value in readings:
                row = MeterReading(id=str(uuid.uuid4()), meter_id=meter.id,
                                   recorded_at=instant(local), value_kwh=Decimal(value),
                                   photo_key=None, photo_type=None, version=1)
                db.add(row)
                reading_ids.append(row.id)
            bill = ElectricityBill(id=str(uuid.uuid4()), meter_id=meter.id,
                                   period_start=period[0], period_end=period[1],
                                   value_kwh=Decimal("100"), amount_ars=None,
                                   file_key="synthetic", file_type="application/pdf", version=1)
            db.add(bill)
            db.flush()
            output[name] = {"domicile": domicile.id, "meter": meter.id,
                            "bill": bill.id, "readings": reading_ids}
        db.commit()
    print(json.dumps(output))


if __name__ == "__main__":
    main()
