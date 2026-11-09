"""Private immutable CU06 objects, separate from CU05 photo reconciliation."""

import fcntl
import os
import re
import stat
from contextlib import contextmanager
from typing import Iterator
from uuid import uuid4

from app.photo_files import _open_directory

_NAME = re.compile(r"cu06-[0-9a-f]{32}\Z", re.ASCII)
MAX_BYTES = 5_000_000
# Fixed deployment-wide advisory key shared by writers and reconciliation.
LOCK_KEY = 7_201_526_506


@contextmanager
def locked_directory(path: str) -> Iterator[int]:
    """Lock a private directory after the caller has acquired its DB lock."""
    directory = _open_directory(path)
    try:
        lock = os.open(".cu06.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600,
                       dir_fd=directory)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield directory
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
        finally:
            os.close(lock)
    finally:
        os.close(directory)


def publish(directory: int, data: bytes) -> str:
    """Durably publish a fresh immutable object without overwriting any file."""
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Invalid file size.")
    temp = f".cu06-{uuid4().hex}.tmp"
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        for _ in range(8):
            name = f"cu06-{uuid4().hex}"
            try:
                os.link(temp, name, src_dir_fd=directory, dst_dir_fd=directory,
                        follow_symlinks=False)
            except FileExistsError:
                continue
            os.unlink(temp, dir_fd=directory)
            os.fsync(directory)
            return name
        raise FileExistsError("Unable to allocate file.")
    except BaseException:
        try:
            os.unlink(temp, dir_fd=directory)
        except FileNotFoundError:
            pass
        raise


def read(directory: int, name: str) -> bytes:
    """Read a bounded regular object without following links."""
    if _NAME.fullmatch(name) is None:
        raise ValueError("Invalid object key.")
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_BYTES:
            raise ValueError("Invalid object.")
        chunks: list[bytes] = []
        total = 0
        while chunk := os.read(descriptor, 65536):
            total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError("Invalid object size.")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)
