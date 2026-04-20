from pynput import keyboard
from common.protocol import pack_keyboard


class KeyboardListener:
    def __init__(self, on_keyboard_event=None):
        self.listener = None
        self.on_keyboard_event = on_keyboard_event
        self._suppress = False

    def start(self):
        self._start_listener()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def set_suppress(self, suppress):
        if self._suppress != suppress:
            self._suppress = suppress
            if self.listener:
                self.listener.stop()
                self.listener = None
            self._start_listener()

    def _start_listener(self):
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=self._suppress
        )
        self.listener.start()

    def _on_press(self, key):
        if self.on_keyboard_event:
            try:
                key_code = key.vk
            except AttributeError:
                try:
                    key_code = key.value.vk
                except AttributeError:
                    return
            data = pack_keyboard(key_code, True)
            self.on_keyboard_event(data)

    def _on_release(self, key):
        if self.on_keyboard_event:
            try:
                key_code = key.vk
            except AttributeError:
                try:
                    key_code = key.value.vk
                except AttributeError:
                    return
            data = pack_keyboard(key_code, False)
            self.on_keyboard_event(data)