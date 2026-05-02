import io
import time
import unittest

from src.controls import ScraperControl


def _control(*lines):
    """Helper: create a ScraperControl fed by a fixed list of input lines."""
    return ScraperControl(
        stdin=io.StringIO("\n".join(lines) + "\n")
    )  # Trailing \n ensures the last line is yielded


class TestCheckInput(unittest.TestCase):
    """Tests for check_input() — driven by putting items directly into the queue."""

    def setUp(self):
        self.control = _control()

    def _feed(self, *keys):
        # Bypasses the stdin thread: writes directly to the queue for fast, deterministic tests.
        for key in keys:
            self.control._queue.put(key)
        self.control.check_input()

    def test_pause(self):
        self._feed("p")
        self.assertTrue(self.control._paused)

    def test_pause_already_paused_has_no_effect(self):
        self.control._paused = True
        self._feed("p")
        self.assertTrue(self.control._paused)

    def test_resume(self):
        self.control._paused = True
        self._feed("r")
        self.assertFalse(self.control._paused)

    def test_resume_when_not_paused_has_no_effect(self):
        self._feed("r")
        self.assertFalse(self.control._paused)

    def test_skip(self):
        self._feed("s")
        self.assertTrue(self.control.skip_artist)
        self.assertFalse(self.control._paused)

    def test_skip_while_paused_also_resumes(self):
        self.control._paused = True
        self._feed("s")
        self.assertTrue(self.control.skip_artist)
        self.assertFalse(self.control._paused)

    def test_quit(self):
        self._feed("q")
        self.assertTrue(self.control.quit)
        self.assertFalse(self.control._paused)

    def test_empty_line_ignored(self):
        self._feed("")
        self.assertFalse(self.control._paused)
        self.assertFalse(self.control.skip_artist)
        self.assertFalse(self.control.quit)

    def test_unknown_key_ignored(self):
        self._feed("x")
        self.assertFalse(self.control._paused)
        self.assertFalse(self.control.skip_artist)
        self.assertFalse(self.control.quit)

    def test_reset_artist(self):
        self.control.skip_artist = True
        self.control.reset_artist()
        self.assertFalse(self.control.skip_artist)


class TestStdinThread(unittest.TestCase):
    """Tests for the background reader thread and prompt()."""

    def test_stdin_feeds_queue(self):
        control = _control("p")
        time.sleep(0.05)  # Let the thread read from StringIO
        control.check_input()
        self.assertTrue(control._paused)

    def test_multiple_commands_via_stdin(self):
        control = _control("p", "s")
        time.sleep(0.05)
        control.check_input()
        # 'p' pauses, then 's' skips and unpauses
        self.assertTrue(control.skip_artist)
        self.assertFalse(control._paused)

    def test_prompt_returns_user_input(self):
        control = _control("hello")
        result = control.prompt("Enter something: ")
        self.assertEqual(result, "hello")

    def test_prompt_returns_empty_for_bare_enter(self):
        control = _control("")
        result = control.prompt("Press Enter: ")
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
