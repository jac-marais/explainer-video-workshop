#!/usr/bin/env python3
"""Check contact sheet order, pixels, labels, columns and empty-input errors."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from sheet import contact_sheet

TOOL = Path(__file__).with_name("sheet.py")


class ContactSheetTests(unittest.TestCase):
    def test_numeric_order_and_multiple_rows(self):
        with tempfile.TemporaryDirectory(prefix="stills-'#") as temporary:
            directory = Path(temporary)
            for name, color in [("t10.png", "blue"), ("t0.png", "red"), ("t2.png", "green")]:
                Image.new("RGB", (8, 4), color).save(directory / name)
            Image.new("RGB", (8, 4), "white").save(directory / "ignored.png")
            output, count = contact_sheet(directory, 2)
            self.assertEqual(count, 3)
            with Image.open(output) as sheet:
                self.assertEqual(sheet.size, (1280, 768))
                self.assertEqual(sheet.getpixel((10, 30)), (255, 0, 0))
                self.assertEqual(sheet.getpixel((650, 30)), (0, 128, 0))
                self.assertEqual(sheet.getpixel((10, 414)), (0, 0, 255))
                self.assertGreater(sheet.crop((0, 0, 200, 24)).getextrema()[0][1], 100)
            self.assertEqual(contact_sheet(directory, 1)[1], 3)
            with Image.open(output) as sheet:
                self.assertEqual(sheet.size, (640, 1152))

    def test_empty_folder_and_invalid_columns(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaisesRegex(ValueError, "no t\\*\\.png"):
                contact_sheet(directory)
            for columns in (0, -1, 1.5):
                with self.subTest(columns=columns), self.assertRaisesRegex(ValueError, "positive integer"):
                    contact_sheet(directory, columns)
            result = subprocess.run([sys.executable, TOOL, directory], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("no t*.png", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_bad_time_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in ("tbad.png", "tnan.png", "tinf.png", "t-1.png"):
                with self.subTest(name=name):
                    fixture = directory / name
                    Image.new("RGB", (2, 2)).save(fixture)
                    with self.assertRaisesRegex(ValueError, "numeric|finite"):
                        contact_sheet(directory)
                    fixture.rename(directory / "ignored.png")


if __name__ == "__main__":
    unittest.main()
