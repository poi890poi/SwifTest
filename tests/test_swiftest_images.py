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


class GenshinImageExampleTests(unittest.TestCase):
    def test_shipped_script_handles_start_enter_or_already_running_without_ocr(self):
        example = Path(__file__).resolve().parents[1] / "examples/genshin"
        images = {p.stem: cv2.imread(str(p)) for p in (example / "assets").glob("*.png")}
        for initial in ("entry", "door", "world"):
            with self.subTest(initial=initial):
                state = {"screen": initial, "loading_reads": 0, "reads": 0}
                taps, launched = [], []

                def frame():
                    state["reads"] += 1
                    if state["reads"] > 50:
                        raise AssertionError("The script did not progress through the fixture.")
                    canvas = np.zeros((360, 640, 3), dtype=np.uint8)
                    name = state["screen"]
                    if name == "loading":
                        state["loading_reads"] += 1
                        state["screen"] = "world"
                        return canvas
                    visible = {"world": ["level"], "map": ["map"],
                               "selected": ["waypoint_title", "teleport"]}.get(name, [name])
                    for i, key in enumerate(visible):
                        asset = images[key]
                        h, w = asset.shape[:2]
                        x, y = (240, 324) if key == "level" else (20, 20 if i == 0 else 200)
                        canvas[y:y+h, x:x+w] = asset
                    return canvas

                def tap(x, y, duration=0):
                    current = state["screen"]
                    expected = {"entry": "entry", "door": "door", "selected": "teleport"}
                    if current in expected:
                        h, w = images[expected[current]].shape[:2]
                        top = 200 if current == "selected" else 20
                        self.assertTrue(20 <= x < 20+w and top <= y < top+h)
                    else:
                        expected_xy = (54, 52) if current == "world" else (319, 179)
                        self.assertEqual((x, y), expected_xy)
                    taps.append(current)
                    state["screen"] = {"entry": "door", "door": "world", "world": "map",
                                       "map": "selected", "selected": "loading"}[current]

                with Session(
                    device=SimpleNamespace(launch=lambda package, activity=None: launched.append(package),
                                           display_size=lambda: (640, 360), tap=tap, close=lambda: None),
                    capture=SimpleNamespace(read=frame, repeat=False, close=lambda: None),
                    base=example, timeout=1, poll_interval=.001,
                ) as session:
                    cases = run_script(example / "test_teleport.py", session)
                    self.assertEqual(cases[0]["status"], "passed", cases)
                    self.assertEqual(session.stats["ocr_calls"], 0)
                    self.assertEqual(session.stats["tree_reads"], 0)
                self.assertEqual(launched, ["com.miHoYo.GenshinImpact"])
                prefix = ["entry", "door"] if initial == "entry" else ["door"] if initial == "door" else []
                self.assertEqual(taps, prefix + ["world", "map", "selected"])
                self.assertEqual(state["loading_reads"], 1)
