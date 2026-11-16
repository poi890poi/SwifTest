"""Workflow waits and single-dispatch contracts."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from swiftest.workflow import TouchSequence, Rule, download_delay, point_for


class WorkflowTests(unittest.TestCase):
    def test_slow_teleport_sends_one_tap_and_requires_consecutive_arrival(self):
        seq = TouchSequence(
            [{"element": "teleport"}],
            {"teleport": Rule("selected", "world", require_loading=True)},
            120,
        )
        tap = Mock()

        def frame(state, second, loading=False):
            return seq.advance(state, loading, lambda step: (10, 20), tap, now=second)

        for second in (0, 5, 20):
            self.assertFalse(frame("selected", second))
        self.assertFalse(frame("world", 22))
        self.assertFalse(frame("unknown", 27, True))
        self.assertFalse(frame("world", 30))
        self.assertFalse(frame("unknown", 31))
        self.assertFalse(frame("world", 32))
        self.assertTrue(frame("world", 33))
        tap.assert_called_once()

    def test_download_poll_uses_reported_remaining_size(self):
        self.assertEqual(download_delay(["10000 KB/s（200 MB / 11200 MB）"], 2), 60)
        self.assertEqual(download_delay(["no progress value"], 6), 6)
        self.assertEqual(download_delay(["10000 KB/s (11199 MB / 11200 MB)"], 2), 1)

    def test_duplicate_template_blocks_touch_until_unique(self):
        import cv2, numpy as np

        sample = np.random.RandomState(13).randint(0, 255, (14, 16, 3)).astype(np.uint8)
        screen = np.zeros((90, 160, 3), dtype=np.uint8)
        screen[30:44, 40:56] = sample
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "target.png")
            cv2.imwrite(path, sample)
            self.assertEqual(point_for({"template": path}, screen, None), (48, 37))
            screen[10:24, 80:96] = sample
            self.assertIsNone(point_for({"template": path}, screen, None))
