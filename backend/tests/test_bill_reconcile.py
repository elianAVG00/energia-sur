"""Synthetic CU06 recovery-planning tests; no deletion occurs here."""

import os
import tempfile
import unittest
from pathlib import Path

from app.bill_files import locked_directory
from app.bill_reconcile import BillRecoveryRequired, plan_recovery

LIVE = "cu06-" + "a" * 32
ORPHAN = "cu06-" + "b" * 32
TEMPORARY = ".cu06-" + "c" * 32 + ".tmp"
CU05_LIVE = "cu05-" + "d" * 32


class BillRecoveryPlanTests(unittest.TestCase):
    def test_protects_references_and_ignores_cu05_objects(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            for name in (LIVE, ORPHAN, TEMPORARY, CU05_LIVE, "unmanaged"):
                Path(root, name).write_bytes(b"synthetic")
            with locked_directory(root) as directory:
                candidates, temporary = plan_recovery(directory, [LIVE, LIVE])
            self.assertEqual(candidates, {ORPHAN})
            self.assertEqual(temporary, {TEMPORARY})
            for name in (LIVE, ORPHAN, TEMPORARY, CU05_LIVE, "unmanaged"):
                self.assertTrue(Path(root, name).is_file())

    def test_missing_reference_blocks_all_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            Path(root, ORPHAN).write_bytes(b"synthetic")
            with locked_directory(root) as directory:
                with self.assertRaises(BillRecoveryRequired):
                    plan_recovery(directory, [LIVE])
            self.assertTrue(Path(root, ORPHAN).is_file())

    def test_managed_symlink_blocks_plan_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            Path(root, ORPHAN).symlink_to("unmanaged-target")
            with locked_directory(root) as directory:
                with self.assertRaises(BillRecoveryRequired):
                    plan_recovery(directory, [])
            self.assertTrue(os.path.islink(Path(root, ORPHAN)))

    def test_invalid_reference_and_managed_directory_block_plan(self) -> None:
        with tempfile.TemporaryDirectory() as root, locked_directory(root) as directory:
            for reference in ("../outside", TEMPORARY, "cu06-" + "A" * 32):
                with self.subTest(reference=reference), self.assertRaises(BillRecoveryRequired):
                    plan_recovery(directory, [reference])
        with tempfile.TemporaryDirectory() as root:
            Path(root, TEMPORARY).mkdir()
            with locked_directory(root) as directory, self.assertRaises(BillRecoveryRequired):
                plan_recovery(directory, [])


if __name__ == "__main__":
    unittest.main()
