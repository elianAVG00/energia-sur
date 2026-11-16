"""Public registration schema and synthetic PostgreSQL/ASGI regressions."""

import asyncio
import os
import subprocess
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import api
from app.main import app
from app.models import Account
from app.schemas import RegistrationInput
from app.security import RegistrationRateLimiter, hash_password, verify_password

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


class RegistrationSchemaTests(unittest.TestCase):
    def test_username_and_password_bounds_and_ascii_allowlist(self) -> None:
        accepted = RegistrationInput(username="Abc_1.-", password="p" * 12)
        self.assertEqual(accepted.username, "Abc_1.-")
        RegistrationInput(username="x" * 32, password="p" * 128)
        for username in ("ab", "x" * 33, "ééé", "abc\n", "a b", "a/b"):
            with self.subTest(username=username), self.assertRaises(ValueError):
                RegistrationInput(username=username, password="p" * 12)
        for password in ("p" * 11, "p" * 129):
            with self.subTest(password_length=len(password)), self.assertRaises(ValueError):
                RegistrationInput(username="valid", password=password)
        with self.assertRaises(ValueError):
            RegistrationInput(username="valid", password="p" * 12, role="admin")

    def test_registration_limiter_has_a_strict_key_cap(self) -> None:
        limiter = RegistrationRateLimiter()
        for index in range(1024):
            self.assertIsNone(limiter.retry_after(f"synthetic-peer-{index}"))
        self.assertEqual(len(limiter._hits), 1024)
        self.assertEqual(limiter.retry_after("synthetic-peer-over-cap"), 900)
        self.assertEqual(len(limiter._hits), 1024)


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class RegistrationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(cls.url)
        cls.username = f"r-{uuid4().hex[:24]}"
        cls.password = "Synthetic-registration-password"
        cls.provisioned_username = f"p-{uuid4().hex[:24]}"
        cls.cli_username = f"cli-{uuid4().hex[:24]}"
        with Session(cls.engine) as db:
            db.add(Account(
                username=cls.provisioned_username,
                password_hash=hash_password(cls.password),
            ))
            db.commit()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {"DATABASE_URL": self.url})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        api.registration_limiter.reset()

    def tearDown(self) -> None:
        api.registration_limiter.reset()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    @staticmethod
    async def _request(
        method: str, path: str, *, json: object = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        ) as client:
            return await client.request(method, path, json=json, headers=headers)

    def request(
        self, method: str, path: str, *, json: object = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return asyncio.run(self._request(method, path, json=json, headers=headers))

    def test_registration_returns_only_user_identity_and_does_not_create_session(self) -> None:
        payload = {"username": self.username, "password": self.password}
        response = self.request("POST", "/register", json=payload, headers=ORIGIN)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.json()), {"id", "username", "role"})
        self.assertEqual(response.json()["username"], self.username)
        self.assertEqual(response.json()["role"], "user")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertNotIn("set-cookie", response.headers)
        self.assertNotIn(self.password, response.text)

        with Session(self.engine) as db:
            account = db.scalar(select(Account).where(Account.username == self.username))
            self.assertIsNotNone(account)
            assert account is not None
            self.assertNotEqual(account.password_hash, self.password)
            self.assertTrue(verify_password(self.password, account.password_hash))
            self.assertEqual(account.role, "user")

        self.assertEqual(self.request("GET", "/session").status_code, 401)
        login = self.request(
            "POST", "/login", json=payload, headers=ORIGIN,
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("set-cookie", login.headers)
        duplicate = self.request("POST", "/register", json=payload, headers=ORIGIN)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(
            duplicate.json(),
            {"detail": "Ya existe una cuenta con ese nombre de usuario."},
        )
        self.assertNotIn(self.password, duplicate.text)

    def test_origin_validation_rate_limit_and_sanitized_validation(self) -> None:
        payload = {"username": self.username + "-bad", "password": self.password}
        for origin in ("", "null", "https://untrusted.invalid", "http://127.0.0.1:5173/"):
            response = self.request(
                "POST", "/register", json=payload,
                headers={"Origin": origin} if origin else None,
            )
            self.assertEqual(response.status_code, 403)
            self.assertNotIn("set-cookie", response.headers)

        invalid = self.request(
            "POST", "/register",
            json={"username": "x", "password": "private-invalid", "role": "admin"},
            headers=ORIGIN,
        )
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(invalid.json(), {"detail": "Revisá los datos ingresados."})
        self.assertNotIn("private-invalid", invalid.text)

        # The existing synthetic provisioned name is valid input and yields 409;
        # each valid attempt counts toward this peer's independent registration limit.
        for _ in range(5):
            response = self.request(
                "POST", "/register",
                json={"username": self.provisioned_username, "password": self.password},
                headers=ORIGIN,
            )
            self.assertEqual(response.status_code, 409)
        limited = self.request(
            "POST", "/register",
            json={"username": f"limited-{uuid4().hex[:16]}", "password": self.password},
            headers=ORIGIN,
        )
        self.assertEqual(limited.status_code, 429)
        self.assertGreaterEqual(int(limited.headers["retry-after"]), 1)
        self.assertEqual(limited.headers["cache-control"], "no-store")
        self.assertNotIn("set-cookie", limited.headers)

    def test_concurrent_duplicate_registration_has_one_winner(self) -> None:
        username = f"race-{uuid4().hex[:24]}"
        barrier = threading.Barrier(2)

        def synchronized_hash(password: str) -> str:
            barrier.wait(timeout=30)
            return hash_password(password)

        def register_once() -> int:
            response = asyncio.run(self._request(
                "POST", "/register",
                json={"username": username, "password": self.password},
                headers=ORIGIN,
            ))
            return response.status_code

        with patch("app.api.hash_password", side_effect=synchronized_hash):
            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(lambda _: register_once(), range(2)))
        self.assertEqual(sorted(outcomes), [201, 409])
        with Session(self.engine) as db:
            self.assertEqual(
                len(list(db.scalars(select(Account).where(Account.username == username)))),
                1,
            )

    def test_existing_cli_style_account_can_still_login(self) -> None:
        result = subprocess.run(
            [
                sys.executable, "-m", "app.provision",
                "--username", self.cli_username, "--password-stdin",
            ],
            input=f"{self.password}\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, "synthetic CLI provisioning failed")
        response = self.request(
            "POST", "/login",
            json={"username": self.cli_username, "password": self.password},
            headers=ORIGIN,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("set-cookie", response.headers)
        self.assertTrue(response.json()["csrf_token"])


if __name__ == "__main__":
    unittest.main()
