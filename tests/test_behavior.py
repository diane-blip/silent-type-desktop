import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from silent_type import windows
from silent_type.state import History, format_text


class RecoveryTests(unittest.TestCase):
    def test_saved_before_outcome_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            first = History(path)
            item = first.add("Client phrase")
            self.assertEqual(History(path).recent()[0][3], "saved")
            first.mark(item, "saved: focus changed")
            self.assertEqual(History(path).recent()[0][2:], ("Client phrase", "saved: focus changed"))

    def test_restore_case_without_changing_words(self):
        self.assertEqual(
            format_text("I WORK AT CYBERDYNE SYSTEMS", ["Cyberdyne Systems"]), "I work at Cyberdyne Systems"
        )
        self.assertEqual(format_text("SARAH CALLS JOHNNY", ["Sarah", "John"]), "Sarah calls johnny")


class InsertionGuards(unittest.TestCase):
    def setUp(self):
        # Unit fixtures must not depend on concurrent physical typing.
        key_state = patch.object(windows, "down", return_value=False)
        key_state.start()
        self.addCleanup(key_state.stop)
        menu = patch.object(windows, "in_menu_mode", return_value=False)
        menu.start()
        self.addCleanup(menu.stop)

    def test_open_app_menu_saves_instead_of_typing_commands(self):
        with (
            patch.object(windows, "target", return_value=(1, 4)),
            patch.object(windows, "modifiers_down", return_value=False),
            patch.object(windows, "in_menu_mode", return_value=True),
            patch.object(windows.user32, "SendInput") as send,
        ):
            self.assertEqual(windows.insert("test", (1, 4)), "saved: app menu was open")
            send.assert_not_called()

    def test_ordinary_keys_and_clicks_do_not_block_delivery(self):
        with (
            patch.object(windows, "target", return_value=(1, 4)),
            patch.object(windows, "modifiers_down", return_value=False),
            patch.object(windows, "down", return_value=True),
            patch.object(windows, "time"),
            patch.object(windows.user32, "SendInput", return_value=2) as send,
        ):
            self.assertEqual(windows.insert("ab", (1, 4)), "typed")
            self.assertEqual(send.call_count, 2)

    def test_target_is_the_top_level_window_only(self):
        with patch.object(windows.user32, "GetForegroundWindow", return_value=77):
            self.assertEqual(windows.target(), 77)

    def test_single_instance_reopens_existing_app(self):
        import uuid

        name = "Local\\SilentTypeAcceptance" + uuid.uuid4().hex
        first = windows.Instance(name)
        second = windows.Instance(name)
        try:
            self.assertFalse(first.exists)
            self.assertTrue(second.exists)
            second.request_open()
            self.assertTrue(first.open_requested())
            self.assertFalse(first.open_requested())
        finally:
            second.close()
            first.close()

    def test_focus_change_never_sends_input(self):
        with (
            patch.object(windows, "target", return_value=(2, 5)),
            patch.object(windows, "modifiers_down", return_value=False),
            patch.object(windows.user32, "SendInput") as send,
        ):
            result = windows.insert("test", (1, 4))
            self.assertTrue(result.startswith("saved:"))
            send.assert_not_called()

    def test_returned_focus_after_change_still_blocks(self):
        with (
            patch.object(windows, "target", return_value=(1, 4)),
            patch.object(windows, "modifiers_down", return_value=False),
            patch.object(windows.user32, "SendInput") as send,
        ):
            windows.insert("test", (1, 4), unchanged=lambda: False)
            send.assert_not_called()

    def test_waits_for_remaining_modifier_then_inserts(self):
        with (
            patch.object(windows, "target", return_value=(1, 4)),
            patch.object(windows, "modifiers_down", side_effect=[True, True, False, False, False]),
            patch.object(windows, "time") as clock,
            patch.object(windows.user32, "SendInput", return_value=2) as send,
        ):
            clock.monotonic.return_value = 0
            waiting = []
            result = windows.insert("x", (1, 4), waiting=lambda: waiting.append(True))
            self.assertEqual(result, "typed")
            self.assertEqual(waiting, [True])
            send.assert_called_once()

    def test_destination_change_during_delivery_stops_remaining_text(self):
        with (
            patch.object(windows, "target", side_effect=[(1, 4), (1, 4), (2, 5)]),
            patch.object(windows, "modifiers_down", return_value=False),
            patch.object(windows, "time"),
            patch.object(windows.user32, "SendInput", return_value=2) as send,
        ):
            self.assertEqual(windows.insert("abc", (1, 4)), "saved: partial input; check destination")
            send.assert_called_once()

    def test_held_modifier_is_distinct_from_focus_failure(self):
        with (
            patch.object(windows, "target", return_value=(1, 4)),
            patch.object(windows, "modifiers_down", return_value=True),
            patch.object(windows, "time") as clock,
            patch.object(windows, "down", return_value=False),
            patch.object(windows.user32, "SendInput") as send,
        ):
            clock.monotonic.side_effect = [0, 6]
            self.assertEqual(windows.insert("x", (1, 4)), "saved: release shortcut keys")
            send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
