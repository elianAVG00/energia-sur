"""Controlled promotion of one existing local account to the admin role."""

import argparse
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Account


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote one existing local account to admin.",
    )
    parser.add_argument("--username", required=True)
    args = parser.parse_args()
    username = str(args.username).strip()
    if not 1 <= len(username) <= 80:
        print("Invalid username.", file=sys.stderr)
        return 1
    try:
        with Session(get_engine()) as session:
            account = session.scalar(
                select(Account).where(Account.username == username),
            )
            if account is None:
                print("Account not found.", file=sys.stderr)
                return 1
            account.role = "admin"
            session.commit()
    except Exception:
        print(
            "Promotion failed; verify configuration or database availability.",
            file=sys.stderr,
        )
        return 1
    print("Account promoted to admin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
