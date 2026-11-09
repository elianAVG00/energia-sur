"""Regression checks for the unavailable OCR safety boundary."""

import dataclasses
import fcntl
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

from app.ocr_worker import (
    OCR_FALLBACK_MESSAGE,
    InvalidOcrCrop,
    private_ocr_runtime,
    recognize_region,
    unavailable_ocr_result,
    valid_crop,
    within_ocr_pixel_limit,
)
from app.photo_validation import InvalidPhoto


@unittest.skipUnless(shutil.which("tesseract"), "Needs local Tesseract executable")
class OcrSyntheticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        environment = patch.dict(os.environ, {"CU05_PHOTO_DIR": self.directory.name})
        environment.start()
        self.addCleanup(environment.stop)

    def image(self, text: str, red: bool = False) -> bytes:
        image = Image.new("RGB", (560, 120), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 75)
        draw.text((20, 5), text, fill="black", font=font)
        if red:
            draw.text((360, 5), "6", fill=(220, 20, 20), font=font)
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    def test_clean_digits(self) -> None:
        result = recognize_region(self.image("56538"), 0, 0, 560, 120)
        self.assertEqual((result.status, result.value_kwh), ("suggested", "56538"))

    def test_browser_canvas_digits_are_not_distorted_by_upscaling(self) -> None:
        image = Path(__file__).parent / "fixtures" / "synthetic-canvas-56538.png"
        result = recognize_region(image.read_bytes(), 0, 0, 560, 120)
        self.assertEqual((result.status, result.value_kwh), ("suggested", "56538"))

    def test_separable_red_fraction(self) -> None:
        result = recognize_region(self.image("12345", red=True), 0, 0, 560, 120)
        self.assertEqual((result.status, result.value_kwh), ("suggested", "12345"))

    def test_white_digits_on_black_with_red_fraction(self) -> None:
        image = Image.new("RGB", (560, 120), "black")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 75)
        draw.text((20, 5), "12345", fill="white", font=font)
        draw.text((360, 5), "6", fill=(220, 20, 20), font=font)
        output = io.BytesIO()
        image.save(output, format="PNG")
        result = recognize_region(output.getvalue(), 0, 0, 560, 120)
        self.assertEqual((result.status, result.value_kwh), ("suggested", "12345"))

    def test_blank_abstains(self) -> None:
        result = recognize_region(self.image(""), 0, 0, 560, 120)
        self.assertEqual(result.status, "abstained")

    def test_red_to_left_is_not_assumed_to_be_fraction(self) -> None:
        image = Image.new("RGB", (560, 120), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 75)
        draw.text((20, 5), "6", fill=(220, 20, 20), font=font)
        draw.text((130, 5), "12345", fill="black", font=font)
        output = io.BytesIO()
        image.save(output, format="PNG")
        result = recognize_region(output.getvalue(), 0, 0, 560, 120)
        self.assertEqual(result.status, "abstained")

    def test_nonfinite_confidence_abstains(self) -> None:
        from app.ocr_worker import _recognise

        with Image.open(io.BytesIO(self.image("56538"))) as image:
            with patch("app.ocr_worker._run_engine", return_value=("56538", float("nan"))):
                self.assertEqual(_recognise(image), ("abstained",))

    def test_saturated_lock_abstains(self) -> None:
        path = os.path.join(self.directory.name, ".cu05-ocr.lock")
        with open(path, "w+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = recognize_region(self.image("56538"), 0, 0, 560, 120)
            self.assertEqual(result.status, "abstained")
            # Invalid bytes must not be inspected while admission is held.
            self.assertEqual(recognize_region(b"invalid", 0, 0, 1, 1).status, "abstained")

    def test_invalid_photo_and_crop_are_reported_after_admission(self) -> None:
        with self.assertRaises(InvalidPhoto):
            recognize_region(b"invalid", 0, 0, 1, 1)
        with self.assertRaises(InvalidOcrCrop):
            recognize_region(self.image("56538"), 559, 0, 2, 10)

    def test_engine_timeout_abstains_and_releases_admission(self) -> None:
        executable = os.path.join(self.directory.name, "tesseract")
        with open(executable, "w", encoding="utf-8") as script:
            script.write(f"#!{sys.executable}\nimport time\ntime.sleep(30)\n")
        os.chmod(executable, 0o700)
        with patch.dict(os.environ, {"PATH": self.directory.name}):
            started = time.monotonic()
            result = recognize_region(self.image("56538"), 0, 0, 560, 120)
        self.assertEqual(result.status, "abstained")
        elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 4.5)
        self.assertLess(elapsed, 12)
        path = os.path.join(self.directory.name, ".cu05-ocr.lock")
        with open(path, "r+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_inherited_lock_survives_parent_until_child_is_killed(self) -> None:
        path = os.path.join(self.directory.name, "parent-death.lock")
        script = '''
import fcntl, os, subprocess, sys
fd = os.open(sys.argv[1], os.O_CREAT | os.O_RDWR, 0o600)
fcntl.flock(fd, fcntl.LOCK_EX)
child = subprocess.Popen([sys.executable, "-c", sys.argv[2], str(os.getpid())],
                         stdout=subprocess.PIPE, pass_fds=(fd,))
assert child.stdout.readline() == b"ready\\n"
print("ready", flush=True)
child.wait()
'''
        child_script = '''
import os, sys, time
from app.ocr_worker import _parent_death_guard
_parent_death_guard(int(sys.argv[1]))
print("ready", flush=True)
time.sleep(30)
'''
        parent = subprocess.Popen(
            [sys.executable, "-c", script, path, child_script], stdout=subprocess.PIPE,
        )
        try:
            assert parent.stdout is not None
            self.assertEqual(parent.stdout.readline(), b"ready\n")
            with open(path, "r+b") as lock:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                parent.kill()
                parent.wait(timeout=5)
                deadline = time.monotonic() + 5
                while True:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            self.fail("Admission lock remained held after parent death")
                        time.sleep(0.05)
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            if parent.stdout is not None:
                parent.stdout.close()

    def test_api_death_during_decode_releases_lock(self) -> None:
        marker = os.path.join(self.directory.name, "decoding")
        script = '''
import io, os, time
from pathlib import Path
from PIL import Image
import app.ocr_worker as worker
inspect = worker.inspect_photo
def delayed(data):
    Path(os.environ["OCR_TEST_MARKER"]).write_text("ready")
    time.sleep(30)
    return inspect(data)
worker.inspect_photo = delayed
if __name__ == "__main__":
    output = io.BytesIO()
    Image.new("RGB", (100, 50), "white").save(output, format="PNG")
    worker.recognize_region(output.getvalue(), 0, 0, 100, 50)
'''
        environment = {**os.environ, "OCR_TEST_MARKER": marker, "PYTHONPATH": os.getcwd()}
        source = os.path.join(self.directory.name, "delayed_decode.py")
        Path(source).write_text(script, encoding="utf-8")
        parent = subprocess.Popen([sys.executable, source], env=environment)
        try:
            deadline = time.monotonic() + 8
            while not os.path.exists(marker):
                if parent.poll() is not None or time.monotonic() >= deadline:
                    self.fail("OCR decoder did not start")
                time.sleep(0.05)
            path = os.path.join(self.directory.name, ".cu05-ocr.lock")
            with open(path, "r+b") as lock:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                parent.kill()
                parent.wait(timeout=5)
                deadline = time.monotonic() + 5
                while True:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            self.fail("Decoder retained admission after API death")
                        time.sleep(0.05)
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)


class OcrGeometryTest(unittest.TestCase):
    def test_private_runtime_rejects_core_and_swap(self) -> None:
        with patch("app.ocr_worker.resource.getrlimit", return_value=(1, 1)):
            self.assertFalse(private_ocr_runtime())
        with patch("app.ocr_worker.resource.getrlimit", return_value=(0, 0)):
            with patch("pathlib.Path.read_text", return_value="max"):
                self.assertFalse(private_ocr_runtime())
            with patch("pathlib.Path.read_text", return_value="0"):
                self.assertTrue(private_ocr_runtime())
            with patch("pathlib.Path.read_text", side_effect=OSError):
                self.assertFalse(private_ocr_runtime())

    def test_crop_edges_and_invalid_rectangles(self) -> None:
        self.assertTrue(valid_crop(100, 80, 0, 0, 100, 80))
        self.assertTrue(valid_crop(100, 80, 99, 79, 1, 1))
        for crop in (
            (-1, 0, 1, 1),
            (0, -1, 1, 1),
            (0, 0, 0, 1),
            (0, 0, 1, 0),
            (99, 79, 2, 1),
            (99, 79, 1, 2),
        ):
            with self.subTest(crop=crop):
                self.assertFalse(valid_crop(100, 80, *crop))
        self.assertFalse(valid_crop(0, 80, 0, 0, 1, 1))
        self.assertFalse(valid_crop(100, -1, 0, 0, 1, 1))

    def test_booleans_are_not_integer_geometry(self) -> None:
        self.assertFalse(valid_crop(100, 80, True, 0, 1, 1))
        self.assertFalse(valid_crop(True, 80, 0, 0, 1, 1))
        self.assertFalse(within_ocr_pixel_limit(True, 10))

    def test_pixel_limit_is_inclusive_and_requires_positive_dimensions(self) -> None:
        self.assertTrue(within_ocr_pixel_limit(5000, 4000))
        self.assertFalse(within_ocr_pixel_limit(5001, 4000))
        self.assertFalse(within_ocr_pixel_limit(0, 4000))
        self.assertFalse(within_ocr_pixel_limit(-1, 4000))


class OcrUnavailableTest(unittest.TestCase):
    def test_exact_fallback_and_no_suggestion(self) -> None:
        result = unavailable_ocr_result()
        self.assertEqual(result.status, "abstained")
        self.assertIsNone(result.value_kwh)
        self.assertEqual(
            result.message,
            "No pudimos identificar con seguridad la lectura del medidor. "
            "Intentá subir una fotografía más clara o ingresá manualmente el valor en kWh",
        )
        self.assertEqual(result.message, OCR_FALLBACK_MESSAGE)

    def test_result_is_immutable_and_repeated_calls_abstain(self) -> None:
        first = unavailable_ocr_result()
        self.assertEqual(first, unavailable_ocr_result())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(first, "status", "suggested")


if __name__ == "__main__":
    unittest.main()
