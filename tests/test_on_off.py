import threading
import unittest
from unittest.mock import Mock, patch

from silent_type.app import App
from silent_type.hold_control import PAIR, HoldControl
from silent_type.session import Signals


def app():
    app = App.__new__(App)
    app.enabled = True
    app.busy = False
    app.signals = Signals()
    app.cancel = app.signals.cancel
    app.preview_stop = threading.Event()
    app.feed = Mock()
    app.tray = Mock()
    app.status = Mock()
    app.show_indicator = Mock()
    app.hold_control = HoldControl()
    return app


class OnOffTests(unittest.TestCase):
    def test_off_releases_the_camera_and_cancels_a_phrase(self):
        a = app()
        a.busy = True
        a.set_enabled(False)
        a.feed.close.assert_called_once()
        self.assertTrue(a.cancel.is_set())
        self.assertTrue(a.preview_stop.is_set())
        a.tray.show.assert_called_with("off")
        self.assertIn("camera released", a.show_indicator.call_args.args[0])

    def test_off_ignores_holds(self):
        a = app()
        a.set_enabled(False)
        a.hold_control.observe(frozenset(), (1, 2), False, 0)
        a.hold_control.observe(PAIR, (1, 2), False, 1)
        start = a.hold_control.observe(PAIR, (1, 2), False, 1.2)[0][1]
        with patch.object(a, "start_phrase") as begin:
            a.hold_event("hold_start", start)
            begin.assert_not_called()

    def test_on_requires_both_keys_up_before_the_next_hold(self):
        a = app()
        a.set_enabled(False)
        a.hold_control.state = "ready"
        a.set_enabled(True)
        self.assertEqual(a.hold_control.state, "waiting")
        self.assertEqual(a.hold_control.observe(PAIR, (1, 2), False, 0), [])
        a.tray.show.assert_called_with("ready")

    def test_tray_stays_gray_while_off(self):
        a = app()
        a.set_enabled(False)
        a.tray_state("ready")
        a.tray.show.assert_called_with("off")

    def test_camera_closes_soon_after_a_phrase_by_default(self):
        from silent_type.state import settings

        with patch("silent_type.state.DATA") as data:
            (data / "settings.json").exists.return_value = False
            self.assertEqual(settings()["camera_warm_seconds"], 15)


if __name__ == "__main__":
    unittest.main()
