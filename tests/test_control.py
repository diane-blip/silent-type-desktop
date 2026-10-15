import multiprocessing as mp
import threading
import time
import unittest
from types import SimpleNamespace

from silent_type.app import App
from silent_type.worker import Cancelled, ManagedRecognizer


def stalled_worker(connection):
    time.sleep(60)


class ControlTests(unittest.TestCase):
    def test_finish_and_cancel_are_separate_states(self):
        app = App.__new__(App)
        app.busy = True
        app.finish = threading.Event()
        app.cancel = threading.Event()
        app.window = SimpleNamespace(set_record_label=lambda _: None)
        app.phase = "recording"
        app.toggle_phrase((1, 2))
        self.assertTrue(app.finish.is_set())
        self.assertFalse(app.cancel.is_set())
        app.phase = "working"
        app.toggle_phrase((1, 2))
        self.assertTrue(app.cancel.is_set())

    def worker(self):
        context = mp.get_context("spawn")
        connection, child = context.Pipe()
        worker = ManagedRecognizer.__new__(ManagedRecognizer)
        worker.connection = connection
        worker.closed = False
        worker.process = context.Process(target=stalled_worker, args=(child,), daemon=True)
        worker.process.start()
        child.close()
        return worker

    def test_stalled_inference_terminates_on_timeout(self):
        worker = self.worker()
        start = time.monotonic()
        try:
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                worker.wait(0.15)
            self.assertFalse(worker.process.is_alive())
            self.assertTrue(worker.closed)
            self.assertLess(time.monotonic() - start, 3)
        finally:
            worker.close()

    def test_cancel_terminates_stalled_inference(self):
        worker = self.worker()
        try:
            with self.assertRaises(Cancelled):
                worker.wait(30, cancelled=lambda: True)
            self.assertFalse(worker.process.is_alive())
        finally:
            worker.close()

    def test_cancel_interrupts_blocked_frame_transfer(self):
        worker = self.worker()
        start = time.monotonic()
        try:
            with self.assertRaises(Cancelled):
                worker.decode(b"x" * (4 * 1024 * 1024), [], cancelled=lambda: time.monotonic() - start > 0.15)
            self.assertFalse(worker.process.is_alive())
            self.assertLess(time.monotonic() - start, 3)
        finally:
            worker.close()


if __name__ == "__main__":
    unittest.main()
