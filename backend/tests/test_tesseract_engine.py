"""Synthetic Tesseract smoke checks, not a reliable meter-identification oracle."""

import io
import shutil
import subprocess
import unittest

from PIL import Image, ImageDraw, ImageFont


def synthetic_digits(text: str) -> bytes:
    image = Image.new("RGB", (500, 120), "white")
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 75)
    ImageDraw.Draw(image).text((15, 5), text, fill="black", font=font)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


@unittest.skipUnless(shutil.which("tesseract"), "Needs local Tesseract executable")
class TesseractSmokeTest(unittest.TestCase):
    def recognize(self, image: bytes) -> str:
        result = subprocess.run(
            ["tesseract", "stdin", "stdout", "--psm", "7", "-c", "tessedit_char_whitelist=0123456789"],
            input=image, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=True,
        )
        return result.stdout.decode("utf-8").strip()

    def test_synthetic_digits(self) -> None:
        self.assertEqual(self.recognize(synthetic_digits("56538")), "56538")

    def test_blank_image_does_not_invent_digits(self) -> None:
        self.assertEqual(self.recognize(synthetic_digits("")), "")
