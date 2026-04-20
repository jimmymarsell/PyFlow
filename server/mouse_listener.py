import time
import threading
from pynput import mouse
from common.protocol import pack_mouse_move, pack_mouse_button, pack_mouse_scroll


BUTTON_MAP = {
    'left': 1,
    'right': 2,
    'middle': 3,
    'x1': 4,
    'x2': 5,
}


class MouseListener:
    MOUSE_MOVE_MIN_DELTA = 1

    def __init__(self, on_mouse_event=None):
        self.listener = None
        self.on_mouse_event = on_mouse_event
        self._last_x = 0
        self._last_y = 0
        self._suppress_next = False
        self._lock = threading.Lock()

    def start(self):
        self.listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def suppress_next(self):
        with self._lock:
            self._suppress_next = True

    def _on_move(self, x, y):
        with self._lock:
            if self._suppress_next:
                self._suppress_next = False
                self._last_x = x
                self._last_y = y
                return

        dx = x - self._last_x
        dy = y - self._last_y

        if abs(dx) < self.MOUSE_MOVE_MIN_DELTA and abs(dy) < self.MOUSE_MOVE_MIN_DELTA:
            return

        self._last_x = x
        self._last_y = y
        if self.on_mouse_event:
            data = pack_mouse_move(x, y)
            self.on_mouse_event(data)

    def _on_click(self, x, y, button, pressed):
        self._last_x = x
        self._last_y = y
        if self.on_mouse_event:
            data = pack_mouse_button(BUTTON_MAP.get(button.name, 0), pressed, x, y)
            self.on_mouse_event(data)

    def _on_scroll(self, x, y, dx, dy):
        self._last_x = x
        self._last_y = y
        if self.on_mouse_event:
            data = pack_mouse_scroll(x, y, dx, dy)
            self.on_mouse_event(data)