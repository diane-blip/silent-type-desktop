import queue
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from silent_type import punctuate as module
from silent_type.app import App


def reply(text):
    return lambda **_: SimpleNamespace(
        stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)]
    )


class PunctuationTests(unittest.TestCase):
    def setUp(self):
        key = patch.object(module, "api_key", return_value="test-key")
        key.start()
        self.addCleanup(key.stop)

    def test_adds_punctuation_without_changing_words(self):
        result = module.punctuate(
            "I learned that was the time what do you think",
            {"punctuate": True},
            create=reply("I learned that was the time. What do you think?"),
        )
        self.assertEqual(result, "I learned that was the time. What do you think?")

    def test_apostrophes_and_capitals_are_punctuation(self):
        self.assertEqual(
            module.punctuate("im sure its fine", {"punctuate": True}, create=reply("I'm sure it's fine.")),
            "I'm sure it's fine.",
        )

    def test_any_changed_added_or_dropped_word_types_the_original(self):
        original = "I learned was that time"
        for changed in (
            "I learned what that time.",
            "I learned was that time today.",
            "I learned that time.",
            "Learned was that time, I.",
            "Sure! I learned was that time.",
        ):
            self.assertEqual(module.punctuate(original, {"punctuate": True}, create=reply(changed)), original)

    def test_failure_disabled_or_missing_key_types_the_original(self):
        def fail(**_):
            raise TimeoutError

        self.assertEqual(module.punctuate("hello there", {"punctuate": True}, create=fail), "hello there")
        self.assertEqual(
            module.punctuate("hello there", {"punctuate": False}, create=reply("Hello there.")), "hello there"
        )
        with patch.object(module, "api_key", return_value=None):
            self.assertEqual(
                module.punctuate("hello there", {"punctuate": True}, create=reply("Hello there.")),
                "hello there",
            )


class KeyLookupTests(unittest.TestCase):
    def test_key_lookup_order_and_env_file_setting(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory) / "other.env"
            other.write_text('# comment\nANTHROPIC_API_KEY="from-other"\n', encoding="utf-8")
            with (
                patch.dict(module.os.environ, {}, clear=True),
                patch.object(module, "ENV_FILE", Path(directory) / "missing.env"),
            ):
                self.assertIsNone(module.api_key({}))
                self.assertEqual(module.api_key({"env_file": str(other)}), "from-other")
                with patch.dict(module.os.environ, {"ANTHROPIC_API_KEY": "from-env"}):
                    self.assertEqual(module.api_key({"env_file": str(other)}), "from-env")


class PrivateStripTests(unittest.TestCase):
    def app(self, review_only):
        app = App.__new__(App)
        app.events = queue.Queue()
        app.root = Mock()
        app.status = Mock()
        app.tray = Mock()
        app.window = Mock()
        app.show_indicator = Mock()
        app.hide_indicator = Mock()
        app.terminal_indicator = False
        app.review_only = review_only
        app.busy = True
        return app

    def test_normal_use_never_shows_the_phrase(self):
        for outcome in ("typed", "saved: focus changed"):
            app = self.app(False)
            app.post("result", (outcome, "My private sentence.", 0))
            app.post("idle")
            app.drain()
            shown = app.show_indicator.call_args.args[0]
            self.assertNotIn("private", shown)
        self.assertIn("in Recents", shown)

    def test_review_test_still_shows_recognized_words(self):
        app = self.app(True)
        app.post("result", ("saved: review test only", "Hello there.", 0))
        app.drain()
        self.assertIn("Hello there.", app.show_indicator.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
