"""CU05 image input primitives. Run decoding only in a bounded worker process."""

import base64
import binascii
import io
import warnings
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

MAX_PHOTO_BYTES = 5_000_000
MAX_PHOTO_PIXELS = 40_000_000
MAX_BASE64_BYTES = ((MAX_PHOTO_BYTES + 2) // 3) * 4
_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class InvalidPhoto(ValueError):
    """An image is malformed, unsupported, or unsafe."""


class PhotoTooLarge(InvalidPhoto):
    """The encoded photo exceeds the approved byte limit."""


@dataclass(frozen=True, slots=True)
class PhotoInfo:
    content_type: str
    width: int
    height: int


def decode_photo(value: str) -> bytes:
    """Decode bounded standard base64 without retaining the encoded input."""
    if not isinstance(value, str) or not value:
        raise InvalidPhoto("Invalid photo.")
    if len(value) > MAX_BASE64_BYTES:
        raise PhotoTooLarge("Photo exceeds byte limit.")
    try:
        result = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise InvalidPhoto("Invalid photo.") from None
    if len(result) > MAX_PHOTO_BYTES:
        raise PhotoTooLarge("Photo exceeds byte limit.")
    if not result:
        raise InvalidPhoto("Invalid photo.")
    return result


def inspect_photo(data: bytes) -> PhotoInfo:
    """Check actual image format and decode validity; caller MUST bound the worker."""
    if len(data) > MAX_PHOTO_BYTES:
        raise PhotoTooLarge("Photo exceeds byte limit.")
    if not data:
        raise InvalidPhoto("Invalid photo.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=list(_FORMATS)) as image:
                format_name = image.format
                width, height = image.size
                if width * height > MAX_PHOTO_PIXELS:
                    raise InvalidPhoto("Photo exceeds pixel limit.")
                image.verify()
            with Image.open(io.BytesIO(data), formats=list(_FORMATS)) as image:
                for index in range(getattr(image, "n_frames", 1)):
                    image.seek(index)
                    if image.width * image.height > MAX_PHOTO_PIXELS:
                        raise InvalidPhoto("Photo exceeds pixel limit.")
                    image.load()
            if format_name not in _FORMATS or width < 1 or height < 1:
                raise InvalidPhoto("Invalid photo.")
            return PhotoInfo(_FORMATS[format_name], width, height)
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning,
            OSError, SyntaxError, ValueError):
        raise InvalidPhoto("Invalid photo.") from None
