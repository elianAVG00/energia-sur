"""Private file primitive tests using synthetic data and temporary directories."""

import os
import tempfile
import unittest

from app.bill_files import MAX_BYTES, locked_directory, publish, read


class BillFilesTests(unittest.TestCase):
    def test_publication_and_confined_read(self) -> None:
        with tempfile.TemporaryDirectory() as path, locked_directory(path) as directory:
            first = publish(directory, b"synthetic-one")
            second = publish(directory, b"synthetic-two")
            self.assertNotEqual(first, second)
            self.assertEqual(read(directory, first), b"synthetic-one")
            with self.assertRaises(ValueError):
                read(directory, "../outside")
            os.symlink(first, "cu06-" + "0" * 32, dir_fd=directory)
            with self.assertRaises(OSError):
                read(directory, "cu06-" + "0" * 32)

    def test_size_and_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as path, locked_directory(path) as directory:
            for data in (b"", b"a" * (MAX_BYTES + 1)):
                with self.subTest(size=len(data)), self.assertRaises(ValueError):
                    publish(directory, data)
            name = publish(directory, b"synthetic")
            self.assertEqual(os.stat(name, dir_fd=directory).st_mode & 0o777, 0o600)
