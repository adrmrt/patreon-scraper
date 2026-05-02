import queue
import sys
import threading
import time

_COMMANDS = [
    ("P", "Pause after current batch"),
    ("R", "Resume"),
    ("S", "Skip to next artist"),
    ("Q", "Quit"),
]


def print_commands():
    print("Controls (type key + Enter while scraping):")
    for key, desc in _COMMANDS:
        print(f"  {key}  —  {desc}")
    print()


class ScraperControl:
    def __init__(self, stdin=None):
        self._paused = False
        self.skip_artist = False
        self.quit = False
        self._queue = queue.Queue()  # Thread-safe bridge between reader and main thread
        self._stdin = stdin or sys.stdin  # Injectable for tests

        t = threading.Thread(target=self._reader, daemon=True)  # Daemon: killed on exit
        t.start()

    def _reader(self):
        for line in self._stdin:
            self._queue.put(line.strip().lower())

    def reset_artist(self):
        self.skip_artist = False

    def prompt(self, message: str) -> str:
        """Blocking user prompt — reads from the shared stdin queue."""
        print(message, end="", flush=True)
        return self._queue.get()

    def check_input(self):
        """Process any pending commands from the queue."""
        while True:
            try:
                key = (
                    self._queue.get_nowait()
                )  # Non-blocking; checking empty() first would race
            except queue.Empty:
                break
            if not key:
                continue  # Discard bare Enters so they don't leak into post-artist prompts
            if key == "p" and not self._paused:
                self._paused = True
                print(
                    "\n[Paused]  Type R + Enter to resume, S to skip artist, Q to quit."
                )
            elif key == "r" and self._paused:
                self._paused = False
                print("[Resumed]\n")
            elif key == "s":
                self.skip_artist = True
                self._paused = False  # Lets wait_if_paused exit
                print("\n[Skipping to next artist after this batch...]\n")
            elif key == "q":
                self.quit = True
                self._paused = False  # Lets wait_if_paused exit
                print("\n[Quitting after this batch...]\n")

    def wait_if_paused(self):
        """Block until the user resumes (or skips/quits)."""
        while self._paused:
            self.check_input()  # Polls so s/q can also break this loop
            time.sleep(0.1)
