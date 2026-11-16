import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from swiftest import Session, TargetNotFoundError, screen_signature, wait_screen_change
from swiftest.intent import execute
from swiftest.screen import ScreenSignature


class Sequence:
    frame_driven = True
    repeat = False

    def __init__(self, images):
        self.images = iter(images)
        self.clock = 0.0
        self.reads = 0

    def read(self):
        self.clock += 0.1
        self.reads += 1
        frame = next(self.images)
        if isinstance(frame, Exception):
            raise frame
        return frame

    def close(self):
        pass


class ScreenChangeTests(unittest.TestCase):
    def test_scrolling_repeating_texture_does_not_alias_to_a_scene_change(self):
        strip = ((np.arange(2400) % 4 < 2) * 255).astype(np.uint8)
        image = np.broadcast_to(strip[None, :, None], (1080, 2400, 3)).copy()
        reference = ScreenSignature.capture(iter([image]))
        self.assertEqual(reference.changed_fraction(np.roll(image, 2, axis=1)), 0)

    def session(self, images):
        stream = Sequence(images)
        clock = patch('swiftest.session.time.monotonic', side_effect=lambda: stream.clock)
        clock.start()
        self.addCleanup(clock.stop)
        session = Session(device=SimpleNamespace(close=lambda: None), capture=stream)
        self.addCleanup(session.close)
        return session, stream

    def test_loading_animation_and_flash_then_unknown_destination(self):
        base = np.zeros((120, 240, 3), np.uint8)
        loading = base.copy()
        loading[10:24, 15:185] = 200
        other = np.full_like(base, (24, 100, 150))
        session, stream = self.session([base, loading, other, base, loading, other, other])
        with session:
            reference = screen_signature()
            result = wait_screen_change(reference, persist=0.09)
        self.assertEqual(stream.reads, 7)
        self.assertGreater(result['changed_fraction'], 0.95)
        self.assertEqual(session.last_valid_result['intent'], 'wait_screen_change')
        self.assertEqual(session.stats['input_events'], 0)
        self.assertEqual(session.stats['ocr_calls'], 0)

    def test_fade_accumulates_against_initial_screen_with_json_step(self):
        images = [np.full((64, 96, 3), v, np.uint8) for v in (0, 8, 16, 22, 30, 38)]
        session, stream = self.session(images)
        outcome = execute(session, {'steps': [{'intent': 'Loading ended',
                           'wait_screen_change': {'persist': 0.05}}]})
        self.assertEqual(outcome['changed_fraction'], 1.0)
        self.assertEqual(stream.reads, 6)

    def test_multisample_reference_suppresses_large_animated_panel(self):
        base = np.zeros((96, 96, 3), np.uint8)
        moving = base.copy()
        moving[:, :48] = 200
        other = np.full_like(base, (80, 10, 50))
        session, stream = self.session([base, moving, base, moving, moving, other, other])
        reference = session.screen_signature(samples=2)
        session.wait_screen_change(reference, persist=0)
        self.assertEqual(stream.reads, 7)

    def test_unstable_reference_and_geometry_change_fail(self):
        base = np.zeros((96, 96, 3), np.uint8)
        session, _ = self.session([base, 255-base, base, base[:50]])
        with self.assertRaisesRegex(ValueError, 'stayed stable'):
            session.screen_signature(samples=2)
        with self.assertRaisesRegex(ValueError, 'geometry'):
            session.wait_screen_change()

    def test_timeout_reports_failed_intent_and_disconnect_propagates(self):
        base = np.zeros((96, 96, 3), np.uint8)
        session, _ = self.session([base, base, base, RuntimeError('disconnected')])
        session.checkpoint('loading')
        reference = session.screen_signature()
        with self.assertRaises(TargetNotFoundError):
            session.wait_screen_change(reference, timeout=0.15)
        self.assertEqual(session.last_valid_result['result'], 'loading')
        with self.assertRaisesRegex(RuntimeError, 'disconnected'):
            session.wait_screen_change(reference)

    def test_invalid_plan_fails_before_any_action(self):
        session, stream = self.session([])
        with self.assertRaises(ValueError):
            execute(session, {'steps': [{'key': 'BACK'}, {'wait_screen_change': {'min_fraction': 0}}]})
        self.assertEqual((stream.reads, session.stats['input_events']), (0, 0))
