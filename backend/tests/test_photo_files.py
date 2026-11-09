"""Synthetic-only tests of no-replace publication, not DB/file consistency."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from app.photo_files import locked_directory, publish


class PhotoFilesTest(unittest.TestCase):
    def test_publish_writes_private_distinct_files(self) -> None:
        with tempfile.TemporaryDirectory() as root, locked_directory(root) as directory:
            first = publish(directory, b"synthetic-a")
            second = publish(directory, b"synthetic-b")
            self.assertNotEqual(first, second)
            self.assertEqual(Path(root, first).read_bytes(), b"synthetic-a")
            self.assertEqual(Path(root, second).read_bytes(), b"synthetic-b")
            self.assertEqual(os.stat(Path(root, first)).st_mode & 0o777, 0o600)

    def test_collision_does_not_overwrite_existing_object(self) -> None:
        with tempfile.TemporaryDirectory() as root, locked_directory(root) as directory:
            collision = UUID("00000000-0000-4000-8000-000000000001")
            temporary = UUID("00000000-0000-4000-8000-000000000002")
            replacement = UUID("00000000-0000-4000-8000-000000000003")
            existing = Path(root, f"cu05-{collision.hex}")
            existing.write_bytes(b"existing")
            with patch("app.photo_files.uuid4", side_effect=[temporary, collision, replacement]):
                result = publish(directory, b"synthetic")
            self.assertEqual(existing.read_bytes(), b"existing")
            self.assertEqual(result, f"cu05-{replacement.hex}")
            self.assertEqual(Path(root, result).read_bytes(), b"synthetic")

    def test_symlink_lock_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            Path(root, ".cu05.lock").symlink_to(Path(root, "target"))
            with self.assertRaises(OSError), locked_directory(root):
                self.fail("A symlink must not be followed")

    def test_symlinked_ancestor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            actual = Path(root, "actual")
            actual.mkdir()
            Path(actual, "photos").mkdir()
            alias = Path(root, "alias")
            alias.symlink_to(actual, target_is_directory=True)
            with self.assertRaises(OSError), locked_directory(str(alias / "photos")):
                self.fail("A symlinked ancestor must not be followed")

    def test_cleanup_error_does_not_replace_publication_error(self) -> None:
        with tempfile.TemporaryDirectory() as root, locked_directory(root) as directory:
            with patch("app.photo_files.os.link", side_effect=OSError("publication failure")), \
                    patch("app.photo_files.os.unlink", side_effect=OSError("cleanup failure")):
                with self.assertRaisesRegex(OSError, "publication failure"):
                    publish(directory, b"synthetic")
