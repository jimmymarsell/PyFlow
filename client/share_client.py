import time
import math
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
    pack_switch
)
from common.mouse_predictor import MousePredictor, ScreenConfig

class ShareClient(TCPClient):
    """
    共享客户端（被控端）
    接收主控端发送的事件并在本地执行
    继承自 TCPClient，复用基础 TCP 连接能力

    架构说明：
    - Server（主控端）：监听本地鼠标/键盘，将事件发送到 Client
    - Client（被控端）：接收事件，在本地执行鼠标/键盘操作

    优化特性：
    - 本地预测：减少网络延迟带来的卡顿感
    - 分辨率缩放：支持不同分辨率屏幕间的坐标转换
    - 自动重连：断开后自动尝试重连
    """
    def __init__(self, host, port):
        """
        初始化共享客户端
        :param host: 服务端地址
        :param port: 服务端端口
        """
        super().__init__()
        self.host = host
        self.port = port
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        self.clipboard_sync = ClipboardSync()
        self.dispatcher = EventDispatcher()

        local_screen = pyautogui.size()
        self.local_screen = ScreenConfig(local_screen.width, local_screen.height)

        self.predictor = MousePredictor(history_size=5)
        self.target_x = 0
        self.target_y = 0
        self.current_x = 0
        self.current_y = 0
        self.interpolation_thread = None
        self.stop_interpolation = threading.Event()
        self._first_move_received = False

        self.reconnect = None
        self._remote_control_active = False
        self._last_edge_check = 0
        self._edge_cooldown_ms = 500
        self._setup_dispatcher()

    def _setup_dispatcher(self):
        """
        设置事件分发器
        """
        self.dispatcher.register(MSG_TYPE_MOUSE_MOVE, self._on_mouse_move)
        self.dispatcher.register(MSG_TYPE_MOUSE_BUTTON, self._on_mouse_button)
        self.dispatcher.register(MSG_TYPE_MOUSE_SCROLL, self._on_mouse_scroll)
        self.dispatcher.register(MSG_TYPE_KEYBOARD, self._on_keyboard)
        self.dispatcher.register(MSG_TYPE_CLIPBOARD, self._on_clipboard)
        self.dispatcher.register(MSG_TYPE_SWITCH, self._on_switch)

    def _start_interpolation(self):
        """
        启动插值线程
        """
        if self.interpolation_thread is not None:
            return
        self.stop_interpolation.clear()
        self.interpolation_thread = threading.Thread(target=self._interpolation_loop, daemon=True)
        self.interpolation_thread.start()

    def _stop_interpolation(self):
        """
        停止插值线程
        """
        self.stop_interpolation.set()
        if self.interpolation_thread is not None:
            self.interpolation_thread.join(timeout=0.5)
            self.interpolation_thread = None

    def _interpolation_loop(self):
        """
        插值循环
        以60Hz的频率平滑移动鼠标到目标位置
        """
        while not self.stop_interpolation.is_set():
            dx = self.target_x - self.current_x
            dy = self.target_y - self.current_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 1:
                time.sleep(0.001)
                continue

            step_x = dx * 0.3
            step_y = dy * 0.3

            if abs(step_x) < 1 and dx != 0:
                step_x = 1 if dx > 0 else -1
            if abs(step_y) < 1 and dy != 0:
                step_y = 1 if dy > 0 else -1

            new_x = int(self.current_x + step_x)
            new_y = int(self.current_y + step_y)

            try:
                self.mouse_controller.move_to(new_x, new_y)
                self.current_x = new_x
                self.current_y = new_y
            except Exception as e:
                print(f"[ShareClient] 移动鼠标失败: {e}")

            time.sleep(0.016)

    def _on_mouse_move(self, x, y):
        """
        处理鼠标移动事件
        """
        self.target_x = x
        self.target_y = y

        if not self._first_move_received:
            self._first_move_received = True
            self.current_x = x
            self.current_y = y
            self.predictor.update(x, y)
            try:
                self.mouse_controller.move_to(x, y)
            except Exception as e:
                print(f"[ShareClient] 移动鼠标失败: {e}")
        else:
            self._check_edge_for_return(x, y)

        self._start_interpolation()

    def _on_mouse_button(self, button, pressed, x, y):
        """
        处理鼠标按钮事件
        """
        self._stop_interpolation()
        self.target_x = x
        self.target_y = y
        self.current_x = x
        self.current_y = y
        self.mouse_controller.click(button, pressed, x, y)

    def _on_mouse_scroll(self, x, y, dx, dy):
        """
        处理鼠标滚动事件
        """
        self.mouse_controller.scroll(x, y, dx, dy)

    def _on_keyboard(self, key_code, pressed):
        """
        处理键盘事件
        """
        self.keyboard_controller.type_key(key_code, pressed)

    def _on_clipboard(self, content):
        """
        处理剪贴板同步
        """
        self.clipboard_sync.update_clipboard(content)

    def _on_switch(self, target_x, target_y, action):
        """
        处理屏幕切换命令

        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            action: 切换动作 (0=切换到远程, 1=返回本地)
        """
        print(f"[ShareClient] 收到切换命令: action={action}, target=({target_x}, {target_y})")

        if action == 0:
            self._stop_interpolation()
            self._remote_control_active = True
            self.target_x = target_x
            self.target_y = target_y
            self.current_x = target_x
            self.current_y = target_y
            try:
                self.mouse_controller.move_to(target_x, target_y)
                print(f"[ShareClient] 鼠标移动到 ({target_x}, {target_y})")
            except Exception as e:
                print(f"[ShareClient] 切换后移动鼠标失败: {e}")
        elif action == 1:
            self._remote_control_active = False
            print(f"[ShareClient] 退出远程控制模式")

    def _check_edge_for_return(self, x, y):
        """
        检查是否到达边缘，准备返回本地
        :param x: 鼠标X坐标
        :param y: 鼠标Y坐标
        """
        if not self._remote_control_active:
            return

        current_time = time.time() * 1000
        if current_time - self._last_edge_check < self._edge_cooldown_ms:
            return

        width = self.local_screen.width
        height = self.local_screen.height
        margin = 10

        return_direction = None

        if x <= margin:
            return_direction = 'left'
        elif x >= width - margin:
            return_direction = 'right'
        elif y <= margin:
            return_direction = 'top'
        elif y >= height - margin:
            return_direction = 'bottom'

        if return_direction:
            self._last_edge_check = current_time
            print(f"[ShareClient] 鼠标到达边缘 {return_direction}，请求返回本地")
            try:
                return_data = pack_switch(x, y, 1)
                self.send_data(return_data)
            except Exception as e:
                print(f"[ShareClient] 发送返回命令失败: {e}")

    def on_data_received(self, data):
        """
        数据接收回调
        """
        self.dispatcher.dispatch(data)

    def connect(self):
        """
        连接到服务端
        """
        if super().connect(self.host, self.port):
            print(f"[ShareClient] 已连接到主控端 {self.host}:{self.port}")
            if self.reconnect:
                self.reconnect.reset_delay()
            return True
        return False

    def start_reconnect(self):
        """
        启动自动重连
        """
        if self.reconnect is None:
            self.reconnect = Reconnect(
                connect_func=self.connect,
                on_reconnecting=lambda attempt, delay: print(f"[ShareClient] 正在重连... (尝试 {attempt}, 等待 {delay:.1f}s)")
            )
            self.reconnect.start()
            print("[ShareClient] 自动重连已启动")

    def stop_reconnect(self):
        """
        停止自动重连
        """
        if self.reconnect:
            self.reconnect.stop()
            self.reconnect = None
            print("[ShareClient] 自动重连已停止")

    def disconnect(self):
        """
        断开连接
        """
        self._stop_interpolation()
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
