import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from silent_type.app import App
from silent_type.hold_control import PAIR, HoldControl
from silent_type.session import Signals


class HeldControlTests(unittest.TestCase):
    def test_machine_specific_mapping_requires_two_distinct_bottom_modifiers(self):
        for pair in ((0xA4,), (0xA4, 0xA4), (0xA1, 0xA4), (0x70, 0xA4)):
            with self.assertRaises(ValueError):
                HoldControl(pair=pair)
        mapped = frozenset((0xA3, 0xA5))
        control = HoldControl(pair=mapped)
        control.observe(frozenset(), (1, 2), False, 0)
        control.observe(mapped, (1, 2), False, 1)
        self.assertEqual(control.observe(mapped, (1, 2), False, 1.5), [("hold_start", (1, (1, 2)))])

    def test_existing_dictate_pair_is_rejected_as_a_configuration(self):
        with self.assertRaisesRegex(ValueError, "belongs to Dictate"):
            HoldControl(pair=(0xA2, 0x5B))

    def test_beginning_dictate_during_recognition_saves_instead_of_typing(self):
        app = App.__new__(App)
        app.instance = SimpleNamespace(open_requested=lambda: False)
        app.stop = threading.Event()
        app.busy = True
        app.manual = False
        app.original = (1, 2)
        app.phase = "working"
        app.hold_control = HoldControl()
        app.cancel = threading.Event()
        app.changed = threading.Event()
        app.post = lambda *_: None
        with (
            patch.object(app.stop, "wait", side_effect=lambda _: app.stop.set()),
            patch("silent_type.app.windows.target", return_value=(1, 2)),
            patch("silent_type.app.windows.down", side_effect=lambda key: key in (0xA2, 0x5B)),
        ):
            app.watch_destination()
        self.assertTrue(app.changed.is_set())
        self.assertFalse(app.cancel.is_set())

    def test_default_pair_is_the_physically_verified_right_ctrl_and_alt(self):
        control = HoldControl()
        self.assertEqual(control.pair, frozenset((0xA3, 0xA5)))
        self.assertEqual(control.label(), "Right Ctrl + Right Alt")

    def start(self):
        control = HoldControl()
        self.assertEqual(control.observe(frozenset(), (1, 2), False, 0), [])
        control.observe(PAIR, (1, 2), False, 0.1)
        event = control.observe(PAIR, (1, 2), False, 0.4)
        self.assertEqual(event, [("hold_start", (1, (1, 2)))])
        return control

    def test_one_start_and_either_key_release_finishes(self):
        for key in PAIR:
            control = self.start()
            for index in range(50):
                self.assertEqual(control.observe(PAIR, (1, 2), False, 0.5 + index * 0.1), [])
            self.assertEqual(control.observe(PAIR - {key}, (1, 2), False, 6), [("hold_finish", 1)])
            self.assertFalse(control.live(1))
            self.assertEqual(control.observe(PAIR, (1, 2), False, 7), [])

    def test_held_at_launch_and_brief_combination_cannot_start(self):
        control = HoldControl()
        self.assertEqual(control.observe(PAIR, (1, 2), False, 0), [])
        self.assertEqual(control.observe(PAIR, (1, 2), False, 3), [])
        control.observe(frozenset(), (1, 2), False, 4)
        control.observe(PAIR, (1, 2), False, 5)
        self.assertEqual(control.observe(frozenset(), (1, 2), False, 5.1), [])

    def test_long_hold_finishes_and_needs_release_to_rearm(self):
        control = self.start()
        self.assertEqual(control.observe(PAIR, (1, 2), False, 23), [("hold_finish", 1)])
        self.assertEqual(control.observe(PAIR, (1, 2), False, 24), [])
        control.observe(frozenset(), (1, 2), False, 25)
        control.observe(PAIR, (1, 2), False, 26)
        self.assertEqual(control.observe(PAIR, (1, 2), False, 26.5), [("hold_start", (2, (1, 2)))])

    def test_focus_change_and_other_keys_cancel_without_rearming(self):
        cases = [(PAIR, (3, 4), False, 1), (PAIR | {0xA2}, (1, 2), False, 1), (PAIR, (1, 2), True, 1)]
        for keys, target, interrupted, now in cases:
            control = self.start()
            self.assertEqual(control.observe(keys, target, interrupted, now), [("hold_cancel", 1)])
            self.assertEqual(control.observe(PAIR, (1, 2), False, now + 1), [])

    def test_dictate_and_left_modifier_pairs_cannot_start_right_pair(self):
        for keys in (frozenset((0xA2, 0x5B)), frozenset((0x5B, 0xA4))):
            control = HoldControl()
            control.observe(frozenset(), (1, 2), False, 0)
            self.assertEqual(control.observe(keys, (1, 2), False, 1), [])
            self.assertEqual(control.observe(keys, (1, 2), False, 5), [])

    def app(self, control):
        app = App.__new__(App)
        app.hold_control = control
        app.accepted_hold = None
        app.busy = False
        app.phase = "idle"
        app.finish = threading.Event()
        app.cancel = threading.Event()

        def start(destination):
            app.busy = True
            app.phase = "starting"

        app.start_phrase = start
        return app

    def test_held_alt_pair_is_masked_so_release_opens_no_menu(self):
        for pair, masked in (((0xA3, 0xA5), True), ((0xA2, 0xA3), False)):
            app = App.__new__(App)
            app.hold_control = HoldControl(pair=pair)
            app.busy = False
            app.preview_stop = threading.Event()
            app.preview_stop.set()
            app.recognizer = object()
            app.signals = Signals()
            app.window = Mock()
            app.feed = Mock()
            app.spawn = Mock()
            with patch("silent_type.app.windows.mask_menu_key") as mask:
                app.recents_open = False
                app.start_phrase((1, 2))
            self.assertEqual(mask.called, masked)

    def test_release_before_ui_dispatch_cannot_open_camera(self):
        control = self.start()
        app = self.app(control)
        control.observe(frozenset(), (1, 2), False, 0.5)
        with patch.object(app, "start_phrase") as start:
            app.hold_event("hold_start", (1, (1, 2)))
            start.assert_not_called()

    def test_release_finishes_only_accepted_phrase_and_cancel_is_separate(self):
        app = self.app(self.start())
        with patch("silent_type.app.windows.target", return_value=(1, 2)):
            app.hold_event("hold_start", (1, (1, 2)))
        self.assertEqual(app.accepted_hold, 1)
        app.hold_event("hold_finish", 2)
        self.assertFalse(app.finish.is_set())
        app.hold_event("hold_finish", 1)
        self.assertTrue(app.finish.is_set())
        self.assertFalse(app.cancel.is_set())
        app.phase = "working"
        app.hold_event("hold_cancel", 1)
        self.assertTrue(app.cancel.is_set())

    def test_busy_manual_recording_is_not_finished_by_ignored_hold(self):
        app = self.app(self.start())
        app.busy = True
        app.phase = "recording"
        with patch.object(app, "start_phrase") as start:
            app.hold_event("hold_start", (1, (1, 2)))
            start.assert_not_called()
        app.hold_event("hold_finish", 1)
        self.assertFalse(app.finish.is_set())

    def test_destination_change_before_ui_dispatch_cannot_open_camera(self):
        app = self.app(self.start())
        with (
            patch("silent_type.app.windows.target", return_value=(3, 4)),
            patch.object(app, "start_phrase") as start,
        ):
            app.hold_event("hold_start", (1, (1, 2)))
            start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
