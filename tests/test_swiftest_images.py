"""Image filenames use the ordinary selector, input and reporting paths."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import cv2
import numpy as np

from swiftest import AmbiguousTargetError, Session
from swiftest.cli import run_script
from swiftest.intent import execute, load_catalog


class ImageScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "assets").mkdir()
        self.button = np.random.default_rng(17).integers(0, 255, (18, 24, 3), dtype=np.uint8)
        cv2.imwrite(str(self.base / "assets/button.PNG"), self.button)
        self.frame = np.zeros((120, 200, 3), dtype=np.uint8)
        self.frame[30:48, 40:64] = self.button
        self.taps = []
        self.session = Session(
            device=SimpleNamespace(close=lambda: None, display_size=lambda: (200, 120),
                                   tap=lambda x, y, duration=0: self.taps.append((x, y))),
            capture=SimpleNamespace(read=lambda: self.frame, repeat=False, close=lambda: None),
            base=self.base, timeout=0,
        )
        self.addCleanup(self.session.close)

    def test_python_and_json_use_script_relative_images_and_postconditions(self):
        path = self.base / "test_image.py"
        path.write_text('from swiftest import touch\n'
                        'touch("assets/button.PNG", expect="assets/button.PNG")\n')
        with self.session:
            cases = run_script(path, self.session)
        self.assertEqual(cases[0]["status"], "passed")
        self.assertEqual(self.taps, [(52, 39)])

    def test_json_images_use_the_same_actions_and_absence_checks(self):
        execute(self.session, {"steps": [{"touch": "assets/button.PNG",
                                          "expect": "assets/button.PNG"}]})
        self.assertEqual(self.taps, [(52, 39)])
        self.frame[:] = 0
        self.assertFalse(self.session.exists("assets/button.PNG"))
        self.assertTrue(self.session.assert_not_exists("assets/button.PNG"))
        self.assertEqual(self.session.stats["ocr_calls"], 0)
        self.assertEqual(self.session.stats["tree_reads"], 0)

    def test_duplicates_and_missing_files_never_dispatch_input(self):
        self.frame[70:88, 120:144] = self.button
        with self.assertRaises(AmbiguousTargetError):
            self.session.touch("assets/button.PNG")
        with self.assertRaises(FileNotFoundError):
            self.session.touch("assets/typo.png", required=False)
        with self.assertRaises(ValueError):
            self.session.touch("unknown_name")
        self.assertEqual(self.taps, [])

    def test_catalog_name_takes_precedence_even_when_it_looks_like_an_image(self):
        catalog = self.base / "ui.json"
        catalog.write_text('{"elements":{"button.png":{"position":[0.5,0.5]}}}')
        load_catalog(self.session, catalog)
        self.session.touch("button.png")
        self.assertEqual(self.taps, [(100, 60)])
        self.assertEqual(self.session.stats["captures"], 0)
