"""Synthetic read-only recovery planning tests, not a deletion or locking test."""

import os
import tempfile
import unittest
from pathlib import Path

from app.photo_files import locked_directory
from app.photo_reconciliation import PhotoRecoveryRequired, plan_recovery

LIVE = "cu05-" + "a" * 32
ORPHAN = "cu05-" + "b" * 32
TEMPORARY = ".cu05-" + "c" * 32 + ".tmp"


class PhotoRecoveryPlanTest(unittest.TestCase):
    def test_inventory_protects_references_and_does_not_delete(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            for name in (LIVE, ORPHAN, TEMPORARY, "unmanaged"):
                Path(root, name).write_bytes(b"synthetic")
            with locked_directory(root) as directory:
                plan = plan_recovery(directory, [LIVE, LIVE])
            self.assertEqual(plan.unreferenced_objects, frozenset({ORPHAN}))
            self.assertEqual(plan.temporary_files, frozenset({TEMPORARY}))
            for name in (LIVE, ORPHAN, TEMPORARY, "unmanaged"):
                self.assertTrue(Path(root, name).is_file())

    def test_missing_reference_blocks_all_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            Path(root, ORPHAN).write_bytes(b"synthetic")
            with locked_directory(root) as directory:
                with self.assertRaises(PhotoRecoveryRequired):
                    plan_recovery(directory, [LIVE])
            self.assertTrue(Path(root, ORPHAN).is_file())

    def test_managed_symlink_blocks_plan_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            Path(root, ORPHAN).symlink_to("unmanaged-target")
            with locked_directory(root) as directory:
                with self.assertRaises(PhotoRecoveryRequired):
                    plan_recovery(directory, [])
            self.assertTrue(os.path.islink(Path(root, ORPHAN)))

    def test_invalid_reference_blocks_plan(self) -> None:
        with tempfile.TemporaryDirectory() as root, locked_directory(root) as directory:
            for reference in ("../outside", TEMPORARY, "cu05-" + "A" * 32):
                with self.subTest(reference=reference), self.assertRaises(PhotoRecoveryRequired):
                    plan_recovery(directory, [reference])

    def test_managed_directory_blocks_plan(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            Path(root, TEMPORARY).mkdir()
            with locked_directory(root) as directory:
                with self.assertRaises(PhotoRecoveryRequired):
                    plan_recovery(directory, [])
