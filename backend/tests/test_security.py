"""Local authentication primitives without real credentials or account storage."""

import unittest

from app.security import (
    DUMMY_HASH,
    hash_password,
    matches_csrf,
    new_token,
    token_hash,
    verify_password,
)


class SecurityTests(unittest.TestCase):
    def test_scrypt_random_salts_and_constant_result_verification(self) -> None:
        first = hash_password("synthetic-only-password")
        second = hash_password("synthetic-only-password")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("synthetic-only-password", first))
        self.assertFalse(verify_password("wrong", first))
        self.assertFalse(verify_password("wrong", DUMMY_HASH))
        self.assertNotIn("synthetic-only-password", first)

    def test_malformed_hash_parameters_are_not_trusted(self) -> None:
        for value in ("", "bad", "scrypt$999999999$8$1$bad", "scrypt$131072$8$1$zz$zz"):
            with self.subTest(value=value):
                self.assertFalse(verify_password("synthetic", value))

    def test_tokens_and_non_ascii_csrf_are_safe(self) -> None:
        first, second = new_token(), new_token()
        self.assertNotEqual(first, second)
        self.assertEqual(len(token_hash(first)), 64)
        self.assertNotEqual(token_hash(first), first)
        self.assertTrue(matches_csrf(first, first))
        self.assertFalse(matches_csrf(second, first))
        self.assertFalse(matches_csrf("é", first))
