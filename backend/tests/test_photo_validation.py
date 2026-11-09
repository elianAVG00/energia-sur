"""Synthetic in-memory image checks, not OCR or storage integration evidence."""

import base64
import io
import unittest

from PIL import Image

from app.photo_validation import (
    MAX_PHOTO_BYTES,
    MAX_PHOTO_PIXELS,
    InvalidPhoto,
    PhotoTooLarge,
    decode_photo,
    inspect_photo,
)


def synthetic_image(format_name: str) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (16, 12), "white").save(output, format=format_name)
    return output.getvalue()


class PhotoValidationTest(unittest.TestCase):
    def test_supported_content_is_detected_not_a_filename(self) -> None:
        for name, expected in (("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")):
            with self.subTest(name=name):
                data = synthetic_image(name)
                self.assertEqual(decode_photo(base64.b64encode(data).decode("ascii")), data)
                photo = inspect_photo(data)
                self.assertEqual((photo.content_type, photo.width, photo.height), (expected, 16, 12))

    def test_invalid_and_oversized_data_are_rejected(self) -> None:
        for data in (b"", b"not an image", synthetic_image("GIF"),
                     synthetic_image("JPEG")[:20], b"0" * (MAX_PHOTO_BYTES + 1)):
            with self.subTest(length=len(data)), self.assertRaises(InvalidPhoto):
                inspect_photo(data)
        for value in ("", "***", "é", base64.b64encode(b"0" * (MAX_PHOTO_BYTES + 1)).decode("ascii")):
            with self.subTest(length=len(value)), self.assertRaises(InvalidPhoto):
                decode_photo(value)

    def test_size_is_distinct_from_malformed_content(self) -> None:
        with self.assertRaises(PhotoTooLarge):
            inspect_photo(b"0" * (MAX_PHOTO_BYTES + 1))
        with self.assertRaises(PhotoTooLarge):
            decode_photo(base64.b64encode(b"0" * (MAX_PHOTO_BYTES + 1)).decode("ascii"))
        with self.assertRaises(InvalidPhoto) as error:
            inspect_photo(b"not an image")
        self.assertNotIsInstance(error.exception, PhotoTooLarge)

    def test_animated_webp_frames_are_read(self) -> None:
        output = io.BytesIO()
        frames = [Image.new("RGB", (8, 8), color) for color in ("red", "blue")]
        frames[0].save(output, format="WEBP", save_all=True, append_images=frames[1:], duration=100)
        self.assertEqual(inspect_photo(output.getvalue()).content_type, "image/webp")

    def test_stored_photo_pixel_boundary(self) -> None:
        for width, accepted in ((8000, True), (8001, False)):
            with self.subTest(width=width):
                output = io.BytesIO()
                Image.new("1", (width, 5000)).save(output, format="PNG")
                self.assertLess(len(output.getvalue()), MAX_PHOTO_BYTES)
                self.assertEqual(8000 * 5000, MAX_PHOTO_PIXELS)
                if accepted:
                    self.assertEqual(inspect_photo(output.getvalue()).width, width)
                else:
                    with self.assertRaises(InvalidPhoto):
                        inspect_photo(output.getvalue())
