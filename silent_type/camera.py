"""One shared camera stream with a short pre-roll, so a held pair records at once.

Opening a webcam and waiting for steady frames takes about two seconds. Doing that
on every hold meant short phrases ended before recording began. The stream stays
open while Silent Type is in use and closes after an idle period; frames live only
in memory and are discarded after each phrase. Recorded frames are kept as JPEG
(about 30 KB each) so a long phrase stays small in memory and in transfer.
"""

import collections
import logging
import threading
import time

import cv2

LOG = logging.getLogger(__name__)


def encode(frame):
    ok, data = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise RuntimeError("Could not store a camera frame.")
    return data.tobytes()


def decode(data):
    import numpy as np

    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


class CameraFeed:
    def __init__(self, index_of, idle_seconds=600, preroll=0.5, max_width=640):
        self.index_of = index_of
        self.idle_seconds = idle_seconds
        self.preroll = preroll
        self.max_width = max_width
        self.lock = threading.Lock()
        self.buffer = collections.deque()
        self.capturing = None
        self.latest = None
        self.live = threading.Event()
        self.stopping = threading.Event()
        self.error = None
        self.thread = None
        self.last_use = time.monotonic()

    def running(self):
        return bool(self.thread and self.thread.is_alive())

    def ensure(self):
        """Start the stream if it is closed. Never blocks on the camera."""
        self.last_use = time.monotonic()
        with self.lock:
            if self.running():
                return
            self.stopping.clear()
            self.live.clear()
            self.error = None
            self.buffer.clear()
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def close(self, wait=2):
        self.stopping.set()
        thread = self.thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=wait)

    def begin(self):
        """Start keeping frames, including the pre-roll from just before the press."""
        self.ensure()
        with self.lock:
            self.capturing = [(encode(frame), moment) for frame, moment in self.buffer]

    def take(self):
        """Frames recorded since the last take; recording continues."""
        with self.lock:
            frames = self.capturing or []
            if self.capturing is not None:
                self.capturing = []
        return frames

    def end(self):
        with self.lock:
            frames, self.capturing = self.capturing or [], None
        self.last_use = time.monotonic()
        return frames

    def run(self):
        from .recognition import open_camera, wait_for_live_frames
        from .worker import Cancelled

        cap = None
        try:
            cap = open_camera(self.index_of())
            wait_for_live_frames(cap, self.stopping.is_set)
            self.live.set()
            LOG.info("Camera live")
            last = 0
            while not self.stopping.is_set():
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError("Camera stopped supplying frames.")
                now = time.monotonic()
                if now - last < 1 / 30:
                    continue
                last = now
                # Bound memory even when a driver ignores requested size/FPS.
                if frame.shape[1] > self.max_width:
                    frame = cv2.resize(
                        frame, (self.max_width, round(frame.shape[0] * self.max_width / frame.shape[1]))
                    )
                with self.lock:
                    self.latest = frame
                    self.buffer.append((frame, now))
                    while self.buffer and now - self.buffer[0][1] > self.preroll:
                        self.buffer.popleft()
                    if self.capturing is not None:
                        self.capturing.append((encode(frame), now))
                    elif now - self.last_use > self.idle_seconds:
                        LOG.info("Camera closed after idle period")
                        break
        except Cancelled:
            pass
        except Exception as exc:
            LOG.exception("Camera")
            self.error = str(exc)
        finally:
            if cap:
                cap.release()
            self.live.clear()
            with self.lock:
                self.buffer.clear()
                self.latest = None
