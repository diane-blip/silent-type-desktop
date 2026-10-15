import time
import unittest
from unittest.mock import patch

from silent_type.camera import CameraFeed


class FakeCapture:
    def __init__(self):
        self.released = False

    def read(self):
        time.sleep(0.01)
        import numpy as np

        return True, np.zeros((480, 640, 3), dtype="uint8")

    def release(self):
        self.released = True


class CameraFeedTests(unittest.TestCase):
    def feed(self, **options):
        capture = FakeCapture()
        feed = CameraFeed(lambda: 0, **options)
        patches = [
            patch("silent_type.recognition.open_camera", return_value=capture),
            patch("silent_type.recognition.wait_for_live_frames"),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(feed.close)
        return feed, capture

    def test_recording_starts_with_pre_roll_from_before_the_press(self):
        feed, _ = self.feed(preroll=0.3)
        feed.ensure()
        self.assertTrue(feed.live.wait(2))
        time.sleep(0.4)
        pressed = time.monotonic()
        feed.begin()
        time.sleep(0.3)
        frames = feed.end()
        times = [moment for _, moment in frames]
        self.assertLess(times[0], pressed - 0.15)
        self.assertGreater(times[-1], pressed + 0.2)
        self.assertTrue(all(b > a for a, b in zip(times, times[1:], strict=False)))
        self.assertIsNone(feed.capturing)

    def test_idle_camera_closes_and_reopens_on_next_use(self):
        feed, capture = self.feed(idle_seconds=0.2)
        feed.ensure()
        self.assertTrue(feed.live.wait(2))
        feed.thread.join(timeout=3)
        self.assertFalse(feed.running())
        self.assertTrue(capture.released)
        self.assertIsNone(feed.latest)
        feed.begin()
        self.assertTrue(feed.live.wait(2))
        self.assertTrue(feed.running())

    def test_camera_failure_is_reported_not_hung(self):
        feed = CameraFeed(lambda: 0)
        with patch("silent_type.recognition.open_camera", side_effect=RuntimeError("Camera unavailable.")):
            feed.ensure()
            feed.thread.join(timeout=2)
        self.assertEqual(feed.error, "Camera unavailable.")
        self.assertFalse(feed.live.is_set())


if __name__ == "__main__":
    unittest.main()
