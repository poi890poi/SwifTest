"""Guarded input must distinguish withheld actions from lost acknowledgements."""
import unittest
from unittest.mock import Mock

from swiftest import DeviceError
from swiftest.guarded import checked_tap


class GuardedTests(unittest.TestCase):
    def setUp(self):
        self.device = Mock()

    def tap(self, x=30):
        return checked_tap(self.device, x, 10, 120, 80, "org.swiftest.variantsfixture", "overlay")

    def test_status_is_checked_without_replaying_input(self):
        for response, expected in [(b"SENT", True), (b"OVERLAY", False), (b"UNSUPPORTED", None)]:
            with self.subTest(response=response):
                self.device.run.return_value = response
                self.assertIs(self.tap(), expected)
        for response in (b"DISPLAY_CHANGED", b"FOCUS_CHANGED", b"STATE_ERROR", b""):
            self.device.run.reset_mock()
            self.device.run.return_value = response
            with self.assertRaises(DeviceError):
                self.tap()
            self.device.run.assert_called_once()
        self.device.run.reset_mock()
        self.device.run.side_effect = DeviceError("lost response")
        with self.assertRaises(DeviceError):
            self.tap()
        self.device.run.assert_called_once()

    def test_invalid_geometry_rejects_before_contact(self):
        for x in (-1, 120, float("nan")):
            with self.assertRaises(ValueError):
                self.tap(x)
        self.device.run.assert_not_called()
