import unittest
from unittest.mock import Mock

from swiftest import Android, DeviceError


class DisplayTests(unittest.TestCase):
    def test_default_viewport_can_follow_inactive_inputs(self):
        device = Mock()
        inactive = b"Viewport INTERNAL: displayId=-1, logicalFrame=[0, 0, 0, 0], isActive=[0]\n"
        other = b"Viewport INTERNAL: displayId=2, logicalFrame=[0, 0, 600, 800], isActive=[1]\n"
        active = b"Viewport INTERNAL: displayId=0, logicalFrame=[0, 0, 1080, 2400], isActive=[1]\n"
        device.run.return_value = inactive + other + active
        self.assertEqual(Android.display_size(device), (1080, 2400))
        device.run.return_value = inactive + other
        with self.assertRaises(DeviceError):
            Android.display_size(device)
        device.run.return_value = b"Viewport INTERNAL: logicalFrame=[0, 0, 720, 1280]"
        self.assertEqual(Android.display_size(device), (720, 1280))
