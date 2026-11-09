"""Private CU05 filesystem primitives; caller must hold the PostgreSQL lock first."""

import fcntl
import logging
import os
from contextlib import contextmanager
from pathlib import PurePosixPath
from typing import Iterator
from uuid import uuid4

_LOGGER = logging.getLogger(__name__)


def _open_directory(path: str) -> int:
    """Open each absolute path component without following symlinks."""
    if not os.path.isabs(path):
        raise ValueError("Photo directory must be absolute.")
    components = PurePosixPath(path).parts
    if ".." in components:
        raise ValueError("Photo directory must not contain parent traversal.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open("/", flags)
    try:
        for component in components[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


@contextmanager
def locked_directory(path: str) -> Iterator[int]:
    """Hold the stable filesystem lock; this alone does not authorize cleanup."""
    directory = _open_directory(path)
    try:
        lock = os.open(".cu05.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=directory)
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
    """Fsync and publish one immutable object without overwriting another file.

    The caller owns database/commit coordination; this does not delete any
    published object or interpret an uncertain database result.
    """
    temporary = f".cu05-{uuid4().hex}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        for _ in range(8):
            name = f"cu05-{uuid4().hex}"
            try:
                os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory,
                        follow_symlinks=False)
            except FileExistsError:
                continue
            os.unlink(temporary, dir_fd=directory)
            os.fsync(directory)
            return name
        raise FileExistsError("Unable to allocate a private photo name.")
    except BaseException:
        # Only our unique temporary name may be removed; a published name stays
        # for reference-checked reconciliation, including if fsync failed.
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass
        except OSError:
            _LOGGER.warning("Photo temporary cleanup failed; reconciliation is required.")
        raise
