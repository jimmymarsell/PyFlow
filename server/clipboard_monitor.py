import time
import threading
import pyperclip
from common.protocol import pack_clipboard


class ClipboardMonitor:
    def __init__(self, on_clipboard_change=None, poll_interval=0.5):
        self.on_clipboard_change = on_clipboard_change
        self.poll_interval = poll_interval
        self._last_content = ""
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        try:
            self._last_content = pyperclip.paste()
        except Exception:
            self._last_content = ""
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def set_last_content(self, content):
        self._last_content = content

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            try:
                current_content = pyperclip.paste()
                if current_content != self._last_content:
                    self._last_content = current_content
                    if self.on_clipboard_change:
                        data = pack_clipboard(current_content)
                        self.on_clipboard_change(data)
            except Exception:
                pass
            self._stop_event.wait(self.poll_interval)

    def get_current_content(self):
        try:
            return pyperclip.paste()
        except Exception:
            return ""