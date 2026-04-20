import time
import threading
import pyautogui
from network.tcp_client import TCPClient
from client.mouse_controller import MouseController
from client.keyboard_controller import KeyboardController
from client.clipboard_sync import ClipboardSync
from client.reconnect import Reconnect
from common.event_dispatcher import EventDispatcher
from common.protocol import (
    MSG_TYPE_MOUSE_MOVE,
    MSG_TYPE_MOUSE_BUTTON,
    MSG_TYPE_MOUSE_SCROLL,
    MSG_TYPE_KEYBOARD,
    MSG_TYPE_CLIPBOARD,
    MSG_TYPE_SWITCH,
    MSG_TYPE_MOUSE_DELTA,
    pack_switch,
    unpack_clipboard
)
from common.mouse_predictor import MousePredictor, ScreenConfig
from server.clipboard_monitor import ClipboardMonitor


class ShareClient(TCPClient):
    """
    共享客户端（被控端）

    远程控制时：接收增量鼠标移动、点击、键盘事件并执行
    非远程控制时：忽略所有鼠标/键盘事件

    剪贴板：
    - 被控端复制内容 → 自动同步到主控端
    - 主控端复制内容 → 自动同步到被控端
    - 内置防回环机制
    """
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        self.clipboard_sync = ClipboardSync()
        self.clipboard_monitor = None
        self.dispatcher = EventDispatcher()

        local_screen = pyautogui.size()
        self.local_screen = ScreenConfig(local_screen.width, local_screen.height)

        self._remote_screen_width = 0
        self._remote_screen_height = 0
        self._remote_control_active = False
        self._last_remote_clipboard = ""

        self.reconnect = None
        self._setup_dispatcher()

    def _setup_dispatcher(self):
        self.dispatcher.register(MSG_TYPE_MOUSE_MOVE, self._on_mouse_move)
        self.dispatcher.register(MSG_TYPE_MOUSE_DELTA, self._on_mouse_delta)
        self.dispatcher.register(MSG_TYPE_MOUSE_BUTTON, self._on_mouse_button)
        self.dispatcher.register(MSG_TYPE_MOUSE_SCROLL, self._on_mouse_scroll)
        self.dispatcher.register(MSG_TYPE_KEYBOARD, self._on_keyboard)
        self.dispatcher.register(MSG_TYPE_CLIPBOARD, self._on_clipboard)
        self.dispatcher.register(MSG_TYPE_SWITCH, self._on_switch)

    def _on_mouse_move(self, x, y):
        if not self._remote_control_active:
            return
        scaled_x, scaled_y = self._scale_to_local(x, y)
        self.mouse_controller.move_to(scaled_x, scaled_y)

    def _on_mouse_delta(self, dx, dy):
        if not self._remote_control_active:
            return
        scale_x = self.local_screen.width / max(self._remote_screen_width, 1)
        scale_y = self.local_screen.height / max(self._remote_screen_height, 1)
        scaled_dx = int(dx * scale_x)
        scaled_dy = int(dy * scale_y)
        current = self.mouse_controller.get_position()
        new_x = max(0, min(current[0] + scaled_dx, self.local_screen.width - 1))
        new_y = max(0, min(current[1] + scaled_dy, self.local_screen.height - 1))
        self.mouse_controller.move_to(new_x, new_y)

    def _on_mouse_button(self, button, pressed, x, y):
        if not self._remote_control_active:
            return
        if x == 0 and y == 0:
            pos = self.mouse_controller.get_position()
            self.mouse_controller.click(button, pressed, pos[0], pos[1])
        else:
            scaled_x, scaled_y = self._scale_to_local(x, y)
            self.mouse_controller.click(button, pressed, scaled_x, scaled_y)

    def _on_mouse_scroll(self, x, y, dx, dy):
        if not self._remote_control_active:
            return
        pos = self.mouse_controller.get_position()
        self.mouse_controller.scroll(pos[0], pos[1], dx, dy)

    def _on_keyboard(self, key_code, pressed):
        if not self._remote_control_active:
            return
        self.keyboard_controller.type_key(key_code, pressed)

    def _on_clipboard(self, content):
        self._last_remote_clipboard = content
        self.clipboard_sync.update_clipboard(content)
        if self.clipboard_monitor:
            self.clipboard_monitor.set_last_content(content)

    def _on_local_clipboard_change(self, data):
        try:
            content = unpack_clipboard(data)
            if content == self._last_remote_clipboard:
                return
        except Exception:
            pass
        self.send_data(data)

    def _scale_to_local(self, x, y):
        if self._remote_screen_width <= 0 or self._remote_screen_height <= 0:
            return x, y
        local_x = int(x * self.local_screen.width / self._remote_screen_width)
        local_y = int(y * self.local_screen.height / self._remote_screen_height)
        local_x = max(0, min(local_x, self.local_screen.width - 1))
        local_y = max(0, min(local_y, self.local_screen.height - 1))
        return local_x, local_y

    def _on_switch(self, target_x, target_y, action, screen_w=0, screen_h=0):
        print(f"[ShareClient] 收到切换命令: action={action}, target=({target_x}, {target_y}), screen=({screen_w}x{screen_h})")

        if action == 0:
            self._remote_control_active = True
            if screen_w > 0 and screen_h > 0:
                self._remote_screen_width = screen_w
                self._remote_screen_height = screen_h
            print(f"[ShareClient] 本地屏幕: {self.local_screen.width}x{self.local_screen.height}, 远程屏幕: {self._remote_screen_width}x{self._remote_screen_height}")
            print(f"[ShareClient] SWITCH原始坐标: ({target_x}, {target_y})")
            scaled_x, scaled_y = self._scale_to_local(target_x, target_y)
            print(f"[ShareClient] 缩放后坐标: ({scaled_x}, {scaled_y})")
            try:
                self.mouse_controller.move_to(scaled_x, scaled_y)
                pos = self.mouse_controller.get_position()
                print(f"[ShareClient] move_to后实际位置: {pos}")
            except Exception as e:
                print(f"[ShareClient] 移动鼠标失败: {e}")
        elif action == 1:
            self._remote_control_active = False
            print(f"[ShareClient] 退出远程控制")

    def on_data_received(self, data):
        self.dispatcher.dispatch(data)

    def connect(self):
        if super().connect(self.host, self.port):
            print(f"[ShareClient] 已连接到主控端 {self.host}:{self.port}")
            if self.reconnect:
                self.reconnect.reset_delay()
            self.clipboard_monitor = ClipboardMonitor(on_clipboard_change=self._on_local_clipboard_change)
            self.clipboard_monitor.start()
            print("[ShareClient] 剪贴板监控已启动")
            return True
        return False

    def start_reconnect(self):
        if self.reconnect is None:
            self.reconnect = Reconnect(
                connect_func=self.connect,
                on_reconnecting=lambda attempt, delay: print(f"[ShareClient] 正在重连... (尝试 {attempt}, 等待 {delay:.1f}s)")
            )
            self.reconnect.start()
            print("[ShareClient] 自动重连已启动")

    def stop_reconnect(self):
        if self.reconnect:
            self.reconnect.stop()
            self.reconnect = None
            print("[ShareClient] 自动重连已停止")

    def disconnect(self):
        if self.clipboard_monitor:
            self.clipboard_monitor.stop()
            self.clipboard_monitor = None
            print("[ShareClient] 剪贴板监控已停止")
        self.stop_reconnect()
        super().disconnect()
        print("[ShareClient] 已断开连接")


if __name__ == "__main__":
    client = ShareClient("127.0.0.1", 12345)
    try:
        if client.connect():
            while client.connected:
                time.sleep(1)
    except KeyboardInterrupt:
        client.disconnect()