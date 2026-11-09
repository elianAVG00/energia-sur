"""Bounded local OCR with an inherited, deployment-wide admission lock."""

import ctypes
import fcntl
import io
import math
import multiprocessing
import os
import resource
import signal
import stat
import subprocess
from dataclasses import dataclass
from functools import partial
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Literal

from PIL import Image, ImageChops, ImageFilter, ImageOps, UnidentifiedImageError

from app.photo_files import _open_directory
from app.photo_store import photo_directory
from app.photo_validation import InvalidPhoto, inspect_photo

OCR_FALLBACK_MESSAGE = (
    "No pudimos identificar con seguridad la lectura del medidor. "
    "Intentá subir una fotografía más clara o ingresá manualmente el valor en kWh"
)
OCR_MAX_PIXELS = 20_000_000
OCR_ENGINE_MEMORY_BYTES = 256 * 1024 * 1024
OCR_WORKER_MEMORY_BYTES = 512 * 1024 * 1024
OCR_ENGINE_TIMEOUT_SECONDS = 5.0
OCR_WORKER_TIMEOUT_SECONDS = 12.0
OCR_MIN_CONFIDENCE = 80.0
OCR_MAX_DIGITS = 12
OCR_MAX_WIDTH = 2000
OCR_MAX_HEIGHT = 1000
_ENGINE_CPU_SECONDS = 6
_WORKER_CPU_SECONDS = 12
_RED_MIN = 90
_RED_DIFFERENCE = 40
_INK_MAX = 100
_WHITE = (255, 255, 255)
_LOCK_FD: int | None = None


class OcrWorkerFailed(RuntimeError):
    """The bounded OCR worker did not produce a trustworthy result."""


class InvalidOcrCrop(ValueError):
    """The requested region does not fit the verified image."""


def valid_crop(
    image_width: int,
    image_height: int,
    x: int,
    y: int,
    width: int,
    height: int,
) -> bool:
    """Check crop geometry against dimensions reported by a verified decoder."""
    values = (image_width, image_height, x, y, width, height)
    if any(type(value) is not int for value in values):
        return False
    return (
        image_width > 0
        and image_height > 0
        and x >= 0
        and y >= 0
        and width > 0
        and height > 0
        and x + width <= image_width
        and y + height <= image_height
    )


def within_ocr_pixel_limit(image_width: int, image_height: int) -> bool:
    """Check the per-frame OCR limit using bounded-decoder dimensions only."""
    return (
        type(image_width) is int
        and type(image_height) is int
        and image_width > 0
        and image_height > 0
        and image_width * image_height <= OCR_MAX_PIXELS
    )


@dataclass(frozen=True, slots=True)
class OcrSuggestion:
    """A confident integer candidate; never saved without explicit confirmation."""

    value_kwh: str
    status: Literal["suggested"] = "suggested"


@dataclass(frozen=True, slots=True)
class OcrAbstention:
    """No reliable integer could be identified."""

    status: Literal["abstained"] = "abstained"
    value_kwh: None = None
    message: str = OCR_FALLBACK_MESSAGE


OcrResult = OcrSuggestion | OcrAbstention


def unavailable_ocr_result() -> OcrAbstention:
    """Return the safe fallback without processing or retaining photo data."""
    return OcrAbstention()


def private_ocr_runtime() -> bool:
    """Fail closed if unconfirmed image bytes could be written to swap or a core."""
    try:
        if resource.getrlimit(resource.RLIMIT_CORE)[0] != 0:
            return False
        # Require a durable limit even if the host currently reports no swap:
        # host swap may be enabled after an OCR request begins.
        return Path("/sys/fs/cgroup/memory.swap.max").read_text(encoding="ascii").strip() == "0"
    except (OSError, ValueError, UnicodeError):
        return False


def _red_mask(image: Image.Image) -> Image.Image:
    """Mark clearly red pixels so fractional digits can be excluded."""
    red, green, blue = image.split()
    return ImageChops.multiply(
        red.point(lambda value: 255 if value >= _RED_MIN else 0),
        ImageChops.multiply(
            ImageChops.subtract(red, green).point(
                lambda value: 255 if value >= _RED_DIFFERENCE else 0
            ),
            ImageChops.subtract(red, blue).point(
                lambda value: 255 if value >= _RED_DIFFERENCE else 0
            ),
        ),
    ).filter(ImageFilter.MaxFilter(3))


def _resize_for_ocr(image: Image.Image) -> Image.Image:
    scale = min(1.0, OCR_MAX_WIDTH / image.width, OCR_MAX_HEIGHT / image.height)
    if scale >= 1.0:
        return image
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def _prepare(image: Image.Image) -> Image.Image | None:
    """Mask red ink, then return a bounded grayscale frame or ``None``."""
    image = _resize_for_ocr(image.convert("RGB"))
    red = _red_mask(image)
    red_box = red.getbbox()
    histogram = ImageOps.grayscale(image).histogram()
    dark_background = sum(histogram[:110]) > image.width * image.height // 2
    background = (0, 0, 0) if dark_background else _WHITE
    masked = image if red_box is None else Image.composite(
        Image.new("RGB", image.size, background), image, red,
    )
    if dark_background:
        ink = ImageOps.grayscale(masked).point(lambda value: 255 if value >= 155 else 0)
    else:
        ink = ImageOps.grayscale(masked).point(lambda value: 255 if value <= _INK_MAX else 0)
    ink_box = ink.getbbox()
    if ink_box is None:
        return None
    # Red fractional digits must be strictly to the right of all integer ink.
    # A left-side or overlapping red region is not a defensible fraction.
    if red_box is not None and red_box[0] < ink_box[2]:
        return None
    gray = ImageOps.autocontrast(ImageOps.grayscale(masked))
    # OpenCV runs only in the bounded child, never in the HTTP process.
    import cv2
    import numpy as np

    cv2.setNumThreads(1)
    pixels = np.asarray(gray)
    if float(np.mean(pixels)) < 110:
        pixels = cv2.bitwise_not(pixels)
    # Resampling already legible characters can alter their shapes. Upscale only
    # short crops; retain the original pixels for larger register crops.
    if image.height < 80:
        pixels = cv2.resize(pixels, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return Image.fromarray(pixels)


def _parse_tsv(output: bytes) -> tuple[str, float] | None:
    try:
        text = output.decode("utf-8")
    except UnicodeDecodeError:
        return None
    words: list[tuple[str, float]] = []
    for line in text.splitlines()[1:]:
        columns = line.split("\t")
        if len(columns) < 12:
            continue
        token = columns[11].strip()
        if not token:
            continue
        try:
            confidence = float(columns[10])
        except ValueError:
            continue
        words.append((token, confidence))
    if len(words) != 1:
        return None
    token, confidence = words[0]
    if not (token.isascii() and token.isdigit()) or len(token) > OCR_MAX_DIGITS:
        return None
    return token, confidence


def _engine_limits(parent_pid: int) -> None:
    _parent_death_guard(parent_pid)
    resource.setrlimit(resource.RLIMIT_AS, (OCR_ENGINE_MEMORY_BYTES, OCR_ENGINE_MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CPU, (_ENGINE_CPU_SECONDS, _ENGINE_CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _run_engine(image: Image.Image) -> tuple[str, float] | None:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    environment = dict(os.environ)
    environment["OMP_THREAD_LIMIT"] = "1"
    command = [
        "tesseract", "stdin", "stdout", "--psm", "7", "-l", "eng",
        "-c", "tessedit_char_whitelist=0123456789", "tsv",
    ]
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=environment, preexec_fn=partial(_engine_limits, os.getpid()),
            pass_fds=(_LOCK_FD,) if _LOCK_FD is not None else (),
        )
    except OSError:
        return None
    try:
        output, _ = process.communicate(buffer.getvalue(), timeout=OCR_ENGINE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
        return None
    except BaseException:
        process.kill()
        process.wait(timeout=2)
        raise
    if process.returncode != 0:
        return None
    return _parse_tsv(output)


def _recognise(image: Image.Image) -> tuple[str, ...]:
    prepared = _prepare(image)
    if prepared is None:
        return ("abstained",)
    result = _run_engine(prepared)
    if result is None:
        return ("abstained",)
    token, confidence = result
    if not math.isfinite(confidence) or confidence < OCR_MIN_CONFIDENCE:
        return ("abstained",)
    return ("suggested", token.lstrip("0") or "0")


def _worker_limits() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (OCR_WORKER_MEMORY_BYTES, OCR_WORKER_MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CPU, (_WORKER_CPU_SECONDS, _WORKER_CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _parent_death_guard(parent_pid: int) -> None:
    """Linux kills this process when its creating parent thread terminates."""
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent_pid:
        raise OcrWorkerFailed("Unable to supervise OCR process.")


def _recognise_bytes(data: bytes, x: int, y: int, width: int, height: int) -> tuple[str, ...]:
    try:
        with Image.open(io.BytesIO(data), formats=["JPEG", "PNG", "WEBP"]) as source:
            if not within_ocr_pixel_limit(source.width, source.height):
                return ("abstained",)
            image = ImageOps.exif_transpose(source)
            image.load()
            if not valid_crop(image.width, image.height, x, y, width, height):
                return ("abstained",)
            crop = image.crop((x, y, x + width, y + height))
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        return ("abstained",)
    return _recognise(crop)


def _send(connection: Connection, message: tuple[object, ...]) -> None:
    try:
        connection.send(message)
    except Exception:
        pass


def _worker(
    connection: Connection, data: bytes, x: int, y: int, width: int, height: int,
    parent_pid: int,
) -> None:
    # Become a group leader so the parent can reap this worker and its engine.
    global _LOCK_FD
    try:
        _parent_death_guard(parent_pid)
        os.setsid()
        _worker_limits()
        directory = _open_directory(photo_directory())
        try:
            _LOCK_FD = os.open(
                ".cu05-ocr.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600,
                dir_fd=directory,
            )
        finally:
            os.close(directory)
        metadata = os.fstat(_LOCK_FD)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise OcrWorkerFailed("Invalid OCR admission lock.")
        fcntl.flock(_LOCK_FD, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["OMP_NUM_THREADS"] = "1"
        try:
            info = inspect_photo(data)
        except InvalidPhoto:
            _send(connection, ("invalid_photo",))
            return
        if not valid_crop(info.width, info.height, x, y, width, height):
            _send(connection, ("invalid_crop",))
            return
        if not within_ocr_pixel_limit(info.width, info.height):
            _send(connection, ("abstained",))
            return
        _send(connection, _recognise_bytes(data, x, y, width, height))
    except BaseException:
        _send(connection, ("abstained",))
    finally:
        if _LOCK_FD is not None:
            os.close(_LOCK_FD)
            _LOCK_FD = None
        connection.close()


def _stop(process: BaseProcess) -> None:
    process.join(timeout=1)
    if process.is_alive() and process.pid is not None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            process.kill()
        process.join(timeout=2)
    if process.is_alive():
        process.kill()
        process.join(timeout=1)
    if process.is_alive():
        raise OcrWorkerFailed("Bounded OCR worker could not be stopped.")


def recognize_region(data: bytes, x: int, y: int, width: int, height: int) -> OcrResult:
    """Run one bounded OCR job in a disposable child and never raise for bad input."""
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_worker, args=(child, data, x, y, width, height, os.getpid()), daemon=True,
    )
    process.start()
    child.close()
    try:
        if not parent.poll(OCR_WORKER_TIMEOUT_SECONDS):
            return OcrAbstention()
        try:
            message = parent.recv()
        except (EOFError, OSError):
            return OcrAbstention()
    finally:
        parent.close()
        _stop(process)
    if message == ("invalid_photo",):
        raise InvalidPhoto("Invalid photo.")
    if message == ("invalid_crop",):
        raise InvalidOcrCrop("Invalid OCR crop.")
    if len(message) == 2 and message[0] == "suggested" and isinstance(message[1], str):
        value = message[1]
        if value.isascii() and value.isdigit() and len(value) <= OCR_MAX_DIGITS:
            return OcrSuggestion(value)
    return OcrAbstention()
