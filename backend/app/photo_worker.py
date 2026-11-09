"""Bounded, disposable worker for CU05 image decoding."""

import multiprocessing
import resource
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess

from app.photo_validation import InvalidPhoto, PhotoInfo, PhotoTooLarge

DECODE_MEMORY_BYTES = 512 * 1024 * 1024
DECODE_TIMEOUT_SECONDS = 10.0
_CPU_SECONDS = 20


class PhotoWorkerFailed(RuntimeError):
    """The bounded decoder did not produce a trustworthy result."""


def _apply_limits() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (DECODE_MEMORY_BYTES, DECODE_MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CPU, (_CPU_SECONDS, _CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _decode(connection: Connection, data: bytes) -> None:
    try:
        _apply_limits()
        from app.photo_validation import inspect_photo

        info = inspect_photo(data)
        connection.send(("ok", info.content_type, info.width, info.height))
    except PhotoTooLarge:
        _send(connection, ("too_large",))
    except InvalidPhoto:
        _send(connection, ("invalid",))
    except BaseException:
        _send(connection, ("failed",))
    finally:
        connection.close()


def _send(connection: Connection, message: tuple[object, ...]) -> None:
    try:
        connection.send(message)
    except Exception:
        pass


def _stop(process: BaseProcess) -> None:
    process.join(timeout=1)
    if process.is_alive():
        process.terminate()
        process.join(timeout=2)
    if process.is_alive():
        process.kill()
        process.join(timeout=1)
    if process.is_alive():
        raise PhotoWorkerFailed("Bounded decoder could not be stopped.")


def validate_photo_bounded(data: bytes) -> PhotoInfo:
    """Decode and validate one photo inside a memory- and time-bounded child."""
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_decode, args=(child, data), daemon=True)
    process.start()
    child.close()
    try:
        if not parent.poll(DECODE_TIMEOUT_SECONDS):
            raise PhotoWorkerFailed("Bounded decoder exceeded its deadline.")
        try:
            status, *rest = parent.recv()
        except (EOFError, OSError):
            raise PhotoWorkerFailed("Bounded decoder terminated unexpectedly.") from None
    finally:
        parent.close()
        _stop(process)
    if status == "too_large":
        raise PhotoTooLarge("Photo exceeds byte limit.")
    if status == "invalid":
        raise InvalidPhoto("Invalid photo.")
    if status != "ok" or len(rest) != 3:
        raise PhotoWorkerFailed("Bounded decoder returned no result.")
    content_type, width, height = rest
    if not isinstance(content_type, str) or type(width) is not int or type(height) is not int:
        raise PhotoWorkerFailed("Bounded decoder returned an invalid result.")
    return PhotoInfo(content_type, width, height)
