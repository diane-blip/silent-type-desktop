import tempfile
import threading
import time
import unittest
from pathlib import Path

from silent_type.camera import decode, encode
from silent_type.hold_control import PAIR, HoldControl
from silent_type.log import append_log, log_path
from silent_type.session import PartReader


class SlowReader:
    def __init__(self, fail=()):
        self.fail = set(fail)
        self.calls = []

    def decode(self, frames, times, cancelled=None):
        index = len(self.calls)
        self.calls.append(len(frames))
        time.sleep(0.05)
        if index in self.fail:
            raise RuntimeError("Face was not visible throughout the phrase.")
        return f"part {index}", 0.05


def part(count):
    return [(b"jpeg", index / 30) for index in range(count)]


class LongPhraseTests(unittest.TestCase):
    def test_parts_are_read_in_order_and_joined(self):
        reader = PartReader(SlowReader(), lambda: False)
        for count in (300, 300, 40):
            reader.add(part(count))
        self.assertEqual(reader.finish(), ("part 0 part 1 part 2", 0))

    def test_one_unreadable_part_keeps_the_rest(self):
        reader = PartReader(SlowReader(fail={1}), lambda: False)
        for _ in range(3):
            reader.add(part(300))
        self.assertEqual(reader.finish(), ("part 0 part 2", 1))

    def test_all_parts_unreadable_reports_the_reason(self):
        reader = PartReader(SlowReader(fail={0}), lambda: False)
        reader.add(part(30))
        with self.assertRaisesRegex(RuntimeError, "Face was not visible"):
            reader.finish()

    def test_cancel_skips_remaining_parts(self):
        cancel = threading.Event()
        recognizer = SlowReader()
        reader = PartReader(recognizer, cancel.is_set)
        cancel.set()
        reader.add(part(30))
        reader.finish()
        self.assertEqual(recognizer.calls, [])

    def test_ten_minute_hold_is_allowed_and_then_finishes(self):
        control = HoldControl(limit=602)
        control.observe(frozenset(), (1, 2), False, 0)
        control.observe(PAIR, (1, 2), False, 1)
        self.assertEqual(control.observe(PAIR, (1, 2), False, 1.2), [("hold_start", (1, (1, 2)))])
        self.assertEqual(control.observe(PAIR, (1, 2), False, 300), [])
        self.assertEqual(control.observe(PAIR, (1, 2), False, 604), [("hold_finish", 1)])

    def test_frames_round_trip_through_compact_storage(self):
        import numpy as np

        frame = np.full((480, 640, 3), 120, dtype=np.uint8)
        data = encode(frame)
        self.assertLess(len(data), 60_000)
        self.assertEqual(decode(data).shape, frame.shape)

    def test_log_matches_dictate_format_with_one_heading_per_day(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "silent-type-log.md"
            append_log("First  phrase", path)
            append_log("Second phrase", path)
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# Silent Type log"))
            self.assertEqual(text.count("\n## "), 1)
            self.assertRegex(text, r"- \*\*\d\d:\d\d\*\* First phrase\n- \*\*\d\d:\d\d\*\* Second phrase\n$")

    def test_log_location_is_configurable(self):
        self.assertEqual(log_path({}).name, "silent-type-log.md")
        self.assertEqual(
            str(log_path({"log_path": "D:/Notes/lips.md"})).replace("\\", "/"), "D:/Notes/lips.md"
        )


if __name__ == "__main__":
    unittest.main()
