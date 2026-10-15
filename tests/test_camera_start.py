import unittest
from types import SimpleNamespace
from unittest.mock import patch

from silent_type.recognition import nearest_face, wait_for_live_frames
from silent_type.worker import Cancelled


class Stream:
    def __init__(self, intervals):
        self.intervals = iter(intervals)
        self.clock = 0
        self.reads = 0

    def read(self):
        self.clock += next(self.intervals)
        self.reads += 1
        return True, None


class CameraStart(unittest.TestCase):
    def test_cached_startup_and_long_gap_do_not_invite_recording(self):
        stream = Stream([0, 0, 0, 0, 0, 0, 1.5] + [0.04] * 10)
        with patch("silent_type.recognition.time.monotonic", side_effect=lambda: stream.clock):
            wait_for_live_frames(stream)
        self.assertGreaterEqual(stream.reads, 14)
        self.assertGreaterEqual(stream.clock, 1.75)

    def test_permanently_slow_camera_fails_before_recording(self):
        stream = Stream([0.5] * 20)
        with (
            patch("silent_type.recognition.time.monotonic", side_effect=lambda: stream.clock),
            self.assertRaisesRegex(RuntimeError, "steady frame rate"),
        ):
            wait_for_live_frames(stream)
        self.assertEqual(stream.clock, 8)

    def test_startup_cancel_does_not_wait_for_camera(self):
        stream = Stream([])
        with self.assertRaises(Cancelled):
            wait_for_live_frames(stream, cancelled=lambda: True)
        self.assertEqual(stream.reads, 0)


def detection(width, height, label):
    return SimpleNamespace(label=label, bounding_box=SimpleNamespace(width=width, height=height))


class SharedSpace(unittest.TestCase):
    def test_person_at_the_camera_is_read_and_passersby_ignored(self):
        faces = [
            detection(0.08, 0.1, "passerby"),
            detection(0.35, 0.45, "you"),
            detection(0.12, 0.15, "table"),
        ]
        self.assertEqual(nearest_face(faces).label, "you")
        self.assertIsNone(nearest_face([]))
        self.assertIsNone(nearest_face(None))


if __name__ == "__main__":
    unittest.main()
