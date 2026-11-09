"""Operation-only launch and spatial selectors, including failure paths."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest

import cv2
import numpy as np

from swiftest import (Absent, AmbiguousTargetError, Box, DeviceError, Dialog,
                      Position, Relative, Session, TargetNotFoundError,
                      Template, Variants)
from swiftest.intent import execute


class Screen:
    """A deterministic fixture selector; each pixel encodes one visible control."""
    def __init__(self, code):
        self.code = code

    def matches(self, obs, scope=None):
        return [Box(int(x), int(y), 1, 1) for y, x in zip(*np.where(obs.image[:, :, 0] == self.code))]


class LaunchTests(unittest.TestCase):
    def make_session(self, frames, timeout=2):
        clock = [0.0]
        pending = iter(frames)
        visible = [frames[-1]]
        taps, launches = [], []

        def read():
            visible[0] = next(pending, visible[0])
            clock[0] += .1
            image = np.zeros((40, 60, 3), dtype=np.uint8)
            for code, x, y in visible[0]:
                image[y, x] = code
            return image

        for timer in (patch('swiftest.session.time.monotonic', lambda: clock[0]),
                      patch('swiftest.session.time.sleep', lambda delay: clock.__setitem__(0, clock[0] + delay))):
            timer.start()
            self.addCleanup(timer.stop)
        device = SimpleNamespace(launch=lambda *args: launches.append(args),
                                 display_size=lambda: (60, 40), close=lambda: None,
                                 tap=lambda x, y, duration=0: taps.append((x, y)))
        session = Session(device=device, timeout=timeout,
                          capture=SimpleNamespace(read=read, repeat=False, close=lambda: None))
        self.addCleanup(session.close)
        return session, taps, launches

    def test_entry_uses_one_observation_per_decision_and_never_repeats_a_sent_button(self):
        start, enter, ready = [(1, 10, 10)], [(2, 30, 10)], [(3, 50, 10)]
        session, taps, launches = self.make_session([start, start, [], enter, enter, ready])
        self.assertTrue(session.open('demo', through=[Screen(1), Screen(2)], expect=Screen(3)))
        self.assertEqual(taps, [(10, 10), (30, 10)])
        self.assertEqual(launches, [('demo', None)])
        self.assertEqual(session.stats['captures'], 6)
        self.assertEqual(session.last_valid_result['confirmation'], 'postcondition')

    def test_already_ready_skips_all_entry_actions(self):
        session, taps, _ = self.make_session([[(3, 50, 10), (1, 10, 10)]])
        session.open('demo', through=[Screen(1), Screen(2)], expect=Screen(3))
        self.assertEqual(taps, [])
        self.assertEqual(session.stats['captures'], 1)

    def test_later_entry_skips_earlier_actions(self):
        session, taps, _ = self.make_session([[(2, 30, 10)], [], [(3, 50, 10)]])
        session.open('demo', through=[Screen(1), Screen(2)], expect=Screen(3))
        self.assertEqual(taps, [(30, 10)])

    def test_unknown_or_stuck_entry_times_out_without_repeating(self):
        for frames, expected in (([[]], []), ([[(1, 10, 10)]], [(10, 10)])):
            with self.subTest(frames=frames):
                session, taps, _ = self.make_session(frames, timeout=.3)
                session.checkpoint('previous result')
                with self.assertRaises(TargetNotFoundError):
                    session.open('demo', through=[Screen(1)], expect=Screen(3))
                self.assertEqual(taps, expected)
                self.assertEqual(session.failed_intent['intent'], 'open')
                self.assertEqual(session.last_valid_result['result'], 'previous result')

    def test_multiple_entry_controls_or_ambiguous_completion_never_authorize_input(self):
        for frame in ([(1, 10, 10), (1, 20, 10)],
                      [(1, 10, 10), (2, 20, 10)],
                      [(3, 10, 10), (3, 20, 10), (1, 30, 10)]):
            with self.subTest(frame=frame):
                session, taps, _ = self.make_session([frame], timeout=0)
                with self.assertRaises(AmbiguousTargetError):
                    session.open('demo', through=[Screen(1), Screen(2)], expect=Screen(3))
                self.assertEqual(taps, [])

    def test_input_guards_and_lost_acknowledgement_propagate_without_replay(self):
        session, taps, _ = self.make_session([[(1, 10, 10)]])
        session.device.display_size = lambda: (60, 41)
        with self.assertRaises(DeviceError):
            session.open('demo', through=[Screen(1)], expect=Screen(3))
        self.assertEqual(taps, [])
        session.device.display_size = lambda: (60, 40)

        def uncertain(*args):
            taps.append(args)
            raise DeviceError('Lost input acknowledgement')

        session.device.tap = uncertain
        with self.assertRaises(DeviceError):
            session.open('demo', through=[Screen(1)], expect=Screen(3))
        self.assertEqual(len(taps), 1)

    def test_invalid_entry_contract_is_rejected_before_launch(self):
        session, taps, launches = self.make_session([[]])
        for options in ({'through': [Screen(1)]}, {'through': 'start.png', 'expect': Screen(3)},
                        {'through': [Absent(Screen(1))], 'expect': Screen(3)},
                        {'expect': Screen(3), 'timeout': -1}):
            with self.subTest(options=options), self.assertRaises((ValueError, TypeError)):
                session.open('demo', **options)
        self.assertEqual(launches, [])
        self.assertEqual(taps, [])

    def test_plain_launch_remains_dispatch_only_and_does_not_capture(self):
        session, taps, launches = self.make_session([[]])
        self.assertIsNone(session.open('demo'))
        self.assertEqual(session.stats['captures'], 0)
        self.assertEqual(session.last_valid_result['confirmation'], 'dispatch')

    def test_known_interruption_is_handled_before_reacquiring_entry(self):
        session, taps, _ = self.make_session([
            [(1, 10, 10)], [(4, 5, 5)], [], [(2, 30, 10)], [(3, 50, 10)]])
        session.on_popup('notice', Screen(4), Position(.5, .5))
        session.open('demo', through=[Screen(1), Screen(2)], expect=Screen(3))
        self.assertEqual(taps, [(10, 10), (5, 5), (30, 10)])
        self.assertEqual(session.stats['captures'], 5)

    def test_json_launch_uses_shared_runtime_and_validates_all_steps_first(self):
        session, taps, launches = self.make_session([[(1, 10, 10)], [(3, 50, 10)]])
        session.register('start', Screen(1))
        session.register('ready', Screen(3))
        launch = {'open': 'demo', 'through': ['start'], 'expect': 'ready'}
        with self.assertRaises(ValueError):
            execute(session, {'steps': [launch, {'open': 'other', 'through': ['start']}]})
        self.assertEqual(launches, [])
        execute(session, {'steps': [launch]})
        self.assertEqual(taps, [(10, 10)])


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        rng = np.random.default_rng(719)
        self.button, self.label = [rng.integers(0, 255, (10, 12, 3), dtype=np.uint8) for _ in range(2)]
        cv2.imwrite(str(self.base / 'button.png'), self.button)
        cv2.imwrite(str(self.base / 'label.png'), self.label)
        self.image = np.zeros((120, 200, 3), dtype=np.uint8)
        self.taps = []
        self.session = Session(base=self.base, timeout=0,
            device=SimpleNamespace(display_size=lambda: (200, 120), close=lambda: None,
                                   tap=lambda x, y, duration=0: self.taps.append((x, y))),
            capture=SimpleNamespace(read=lambda: self.image.copy(), repeat=False, close=lambda: None))
        self.addCleanup(self.session.close)

    def place(self, asset, x, y):
        h, w = asset.shape[:2]
        self.image[y:y+h, x:x+w] = asset

    def test_relative_button_uses_fresh_anchor_and_rejects_wrong_side_distractor(self):
        for shift in (0, 60):
            self.image[:] = 0
            self.place(self.label, 40 + shift, 40)
            self.place(self.button, 40 + shift, 10)
            self.place(self.button, 40 + shift, 70)
            before = self.session.stats['captures']
            self.session.touch(Relative('button.png', below='label.png'))
            self.assertEqual(self.taps[-1], (46 + shift, 75))
            self.assertEqual(self.session.stats['captures'] - before, 1)

    def test_missing_or_duplicate_anchor_and_duplicate_valid_buttons_withhold_input(self):
        self.place(self.button, 40, 70)
        with self.assertRaises(TargetNotFoundError):
            self.session.touch(Relative('button.png', below='label.png'))
        self.place(self.label, 40, 40)
        self.place(self.label, 100, 40)
        with self.assertRaises(TargetNotFoundError):
            self.session.touch(Relative('button.png', below='label.png'))
        self.image[40:50, 100:112] = 0
        self.place(self.button, 100, 70)
        with self.assertRaises(AmbiguousTargetError):
            self.session.touch(Relative('button.png', below='label.png'))
        self.assertEqual(self.taps, [])

    def test_directions_distance_and_template_anchor_compose(self):
        self.place(self.label, 80, 40)
        self.place(self.button, 110, 70)
        selector = Relative(Template('button.png', anchor=(0, 0)),
                            below='label.png', right_of='label.png', near='label.png', distance=.4)
        self.session.touch(selector)
        self.assertEqual(self.taps, [(110, 70)])
        for target in (Relative('button.png', above='label.png'),
                       Relative('button.png', left_of='label.png'),
                       Relative('button.png', near='label.png', distance=.1),
                       Relative(Template('button.png', threshold=.5, region=(0, 0, .4, 1)), below='label.png')):
            self.assertFalse(self.session.exists(target))

    def test_filename_composition_preserves_variants_dialog_geometry_and_json(self):
        self.place(self.label, 40, 40)
        self.place(self.button, 40, 70)
        self.session.touch(Variants('button.png', 'button.png'))
        self.session.touch(Dialog('label.png', Position(1, 0)))
        self.assertEqual(self.taps, [(46, 75), (51, 40)])
        execute(self.session, {'steps': [{'touch': {'relative': {
            'target': 'button.png', 'below': 'label.png'}}}]})
        self.assertEqual(self.taps[-1], (46, 75))
        self.image[:] = 0
        self.place(self.label, 100, 80)
        self.session.touch(Dialog('label.png', Position(1, 0)))
        self.assertEqual(self.taps[-1], (111, 80))

    def test_invalid_relations_cannot_be_used_as_input_targets(self):
        for options in ({}, {'near': 'label.png', 'distance': -1},
                        {'near': 'label.png', 'distance': float('nan')}):
            with self.assertRaises(ValueError):
                Relative('button.png', **options)
        with self.assertRaises(ValueError):
            self.session.touch(Relative('button.png', below=Absent('label.png')))
        self.session.register('missing', Absent('label.png'))
        for target in (Relative('button.png', below='missing'),
                       Dialog('label.png', 'missing'), Variants('button.png', 'missing')):
            with self.assertRaises(ValueError):
                self.session.touch(target)
        self.assertEqual(self.taps, [])
