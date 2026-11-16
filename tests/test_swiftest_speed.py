"""Latency controls retain default OCR behavior and bounded workflow input."""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from swiftest.ocr import LocalOCR
from swiftest.workflow import interval
from benchmarks.android.frame_analysis import brightness_percentile, ocr_image


class SpeedTests(unittest.TestCase):
    def test_histogram_preserves_percentile_and_dimmed_pixels(self):
        import cv2

        rng = np.random.default_rng(6481)
        images = [rng.integers(0, 256, (91, 147, 3), dtype=np.uint8),
                  rng.integers(0, 60, (51, 71, 3), dtype=np.uint8),
                  np.arange(200, dtype=np.uint8).reshape(10, 20),
                  np.zeros((1, 1, 3), np.uint8),
                  np.full((11, 12, 3), 4, np.uint8)]
        images += [images[0][::2, ::2], images[1].astype(np.float32)]
        for image in images:
            level = float(np.percentile(image, 99.5))
            self.assertAlmostEqual(brightness_percentile(image), level, places=10)
            expected = cv2.convertScaleAbs(image, alpha=min(16., 230. / level)) if 3 < level < 65 else image
            np.testing.assert_array_equal(ocr_image(image), expected)

    def test_ocr_configuration_is_lazy_and_keeps_original_coordinates(self):
        factory = Mock()
        factory.return_value.return_value = ([([[120, 30], [240, 30], [240, 60], [120, 60]],
                                              "Continue", .98)], None)
        with patch.dict(sys.modules, {"rapidocr_onnxruntime": SimpleNamespace(RapidOCR=factory)}):
            normal = LocalOCR(backend="cpu")
            fast = LocalOCR(max_side=1280, threads=4, backend="cpu")
            factory.assert_not_called()
            normal(np.zeros((100, 200, 3), np.uint8))
            self.assertEqual(factory.call_args.kwargs,
                             dict(intra_op_num_threads=2, inter_op_num_threads=1))
            words = fast(np.zeros((1080, 2400, 3), np.uint8))
            self.assertEqual(factory.call_args.kwargs, dict(intra_op_num_threads=4,
                inter_op_num_threads=1, max_side_len=1280, det_limit_type="max"))
            self.assertEqual(words[0][1].center, (180, 45))
            self.assertEqual(factory.return_value.call_args.args[0].shape, (1080, 2400, 3))

    def test_ocr_rejects_invalid_limits(self):
        for settings in ({"threads": 0}, {"threads": True}, {"max_side": 0},
                         {"max_side": 1280.5}, {"max_side": True}):
            with self.assertRaises(ValueError):
                LocalOCR(**settings)

    def test_interactive_cap_does_not_speed_up_known_downloads(self):
        self.assertEqual(interval("unknown", 10, False), 6)
        self.assertEqual(interval("unknown", 10, False, max_interactive=.25), .25)
        self.assertEqual(interval("world", 10, True, max_interactive=.25), .25)
        for state in ("downloading", "preparing"):
            self.assertEqual(interval(state, 10, False, max_interactive=.25), 20)
        for value in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                interval("world", 0, False, max_interactive=value)
