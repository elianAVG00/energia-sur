"""Controlled local provisioning; credentials are read privately, never arguments."""

import argparse
import getpass
import sys

from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Account
from app.security import hash_password


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision one local CU09 account.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password-stdin", action="store_true")
    args = parser.parse_args()
    username = str(args.username).strip()
    password = sys.stdin.readline().rstrip("\r\n") if args.password_stdin else getpass.getpass()
    if not 1 <= len(username) <= 80 or not 1 <= len(password) <= 1024:
        print("Invalid account input.", file=sys.stderr)
        return 1
    try:
        with Session(get_engine()) as session:
            session.add(Account(username=username, password_hash=hash_password(password)))
            session.commit()
    except Exception:
        print("Account provisioning failed; verify configuration or duplicate username.", file=sys.stderr)
        return 1
    print("Account provisioned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
