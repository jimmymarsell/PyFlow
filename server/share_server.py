import socket
import time
import ctypes
import platform
import pyperclip
from network.tcp_server import TCPServer
from client.mouse_controller import MouseController
from server.mouse_listener import MouseListener
from server.keyboard_listener import KeyboardListener
from server.clipboard_monitor import ClipboardMonitor
from server.screen_edge import ScreenEdge
from server.screen_layout import ScreenLayout, LayoutManager, SwitchController, SwitchState, CoordinateMapper
from common.event_dispatcher import EventDispatcher
from common.protocol import (
    pack_switch,
    pack_mouse_delta,
    pack_mouse_button,
    pack_mouse_scroll,
    MSG_TYPE_MOUSE_MOVE,
    MSG_TYPE_MOUSE_BUTTON,
    MSG_TYPE_MOUSE_SCROLL,
    MSG_TYPE_MOUSE_DELTA,
    MSG_TYPE_KEYBOARD,
    MSG_TYPE_CLIPBOARD,
    MSG_TYPE_SWITCH,
    unpack_mouse_move,
    unpack_mouse_button,
    unpack_mouse_scroll,
    unpack_clipboard,
    get_msg_type
)
from common.system_utils import hide_cursor, show_cursor, get_screen_size

_IS_WINDOWS = platform.system() == 'Windows'
if _IS_WINDOWS:
    from server.mouse_hook import MouseHook


class ShareServer(TCPServer):
    """
    共享服务端（主控端）

    远程控制模式：
    - Windows: 使用低级鼠标钩子(WH_MOUSE_LL)拦截所有鼠标事件
      钩子回调中计算增量并直接发送到被控端，事件不传递给OS
      光标被强制移到屏幕中心，用户看到的本地光标不动
    - 其他平台: 使用 pynput 监听 + 隐藏光标 + 回中重定位方案

    键盘：
    - 远程模式: 隐藏光标 + 启用键盘抑制(suppress)，所有按键只转发被控端，本地不响应
    - 本地模式: 键盘正常工作

    剪贴板：
    - 主控端复制 → 自动同步到被控端
    - 被控端复制 → 自动同步到主控端
    - 内置防回环机制，避免双方互相触发无限同步
    """

    REPOSITION_MARGIN = 80
    RETURN_EDGE_MARGIN = 10

    def __init__(self, host="0.0.0.0", port=12345, config_path=None):
        super().__init__(host, port)
        self.mouse_controller = MouseController()
        self.mouse_listener = None
        self.keyboard_listener = None
        self.clipboard_monitor = None
        self._screen_edge = None
        self._client_socket = None
        self._client_addr = None
        self._mouse_hook = None

        self.layout_manager = LayoutManager(config_path)
        self.switch_controller = None
        self._dispatcher = EventDispatcher()
        self._setup_dispatcher()
        self._init_switch_controller()

        self._prev_x = 0
        self._prev_y = 0
        self._cursor_hidden = False
        self._switch_grace_until = 0
        self._screen_width = 1920
        self._screen_height = 1080
        self._screen_center_x = 960
        self._screen_center_y = 540
        self._update_screen_size()

        self._remote_x = 0
        self._remote_y = 0
        self._remote_w = 0
        self._remote_h = 0

        self._last_remote_clipboard = ""

    def _update_screen_size(self):
        try:
            w, h = get_screen_size()
            self._screen_width = w
            self._screen_height = h
            self._screen_center_x = w // 2
            self._screen_center_y = h // 2
        except Exception:
            pass

    # ===== 钩子回调（Windows 远程模式） =====

    def _on_hook_move(self, dx, dy):
        if abs(dx) >= 1 or abs(dy) >= 1:
            self._send_to_client(pack_mouse_delta(dx, dy))

        target = self.switch_controller.target_screen if self.switch_controller else None
        if target:
            scale_x = target.width / self._screen_width
            scale_y = target.height / self._screen_height
            self._remote_x += dx * scale_x
            self._remote_y += dy * scale_y
            self._remote_x = max(0, min(int(self._remote_x), target.width - 1))
            self._remote_y = max(0, min(int(self._remote_y), target.height - 1))
            self._check_remote_edge()

    def _on_hook_button(self, button, pressed):
        self._send_to_client(pack_mouse_button(button, pressed, 0, 0))

    def _on_hook_scroll(self, dx, dy):
        self._send_to_client(pack_mouse_scroll(0, 0, dx, dy))

    # ===== pynput 回调 =====

    def _on_mouse_event(self, data):
        msg_type = get_msg_type(data)

        if self.switch_controller and self.switch_controller.is_remote_control():
            if not _IS_WINDOWS:
                if msg_type == MSG_TYPE_MOUSE_MOVE:
                    x, y = unpack_mouse_move(data)
                    dx = x - self._prev_x
                    dy = y - self._prev_y

                    if abs(dx) >= 1 or abs(dy) >= 1:
                        self._send_to_client(pack_mouse_delta(dx, dy))
                        self._prev_x = x
                        self._prev_y = y

                        target = self.switch_controller.target_screen if self.switch_controller else None
                        if target:
                            scale_x = target.width / self._screen_width
                            scale_y = target.height / self._screen_height
                            self._remote_x += dx * scale_x
                            self._remote_y += dy * scale_y
                            self._remote_x = max(0, min(int(self._remote_x), target.width - 1))
                            self._remote_y = max(0, min(int(self._remote_y), target.height - 1))
                            self._check_remote_edge()

                        near_edge = (x < self.REPOSITION_MARGIN or
                                     x > self._screen_width - self.REPOSITION_MARGIN or
                                     y < self.REPOSITION_MARGIN or
                                     y > self._screen_height - self.REPOSITION_MARGIN)
                        if near_edge:
                            self._reposition_cursor()

                elif msg_type == MSG_TYPE_MOUSE_BUTTON:
                    button, pressed, x, y = unpack_mouse_button(data)
                    self._send_to_client(pack_mouse_button(button, pressed, 0, 0))
                elif msg_type == MSG_TYPE_MOUSE_SCROLL:
                    x, y, dx, dy = unpack_mouse_scroll(data)
                    self._send_to_client(pack_mouse_scroll(0, 0, dx, dy))

            return

        if msg_type == MSG_TYPE_MOUSE_MOVE:
            x, y = unpack_mouse_move(data)
            self._prev_x = x
            self._prev_y = y
            if time.time() * 1000 >= self._switch_grace_until:
                if self.switch_controller:
                    self.switch_controller.on_mouse_move(x, y)
                if self._screen_edge:
                    self._screen_edge.update(x, y)

    def _on_keyboard_event(self, data):
        if self.switch_controller and self.switch_controller.is_remote_control():
            self._send_to_client(data)
            return

    def _on_clipboard_change(self, data):
        try:
            content = unpack_clipboard(data)
            if content == self._last_remote_clipboard:
                return
        except Exception:
            pass
        self._send_to_client(data)

    def _on_clipboard_from_client(self, content):
        self._last_remote_clipboard = content
        try:
            pyperclip.copy(content)
        except Exception:
            pass
        if self.clipboard_monitor:
            self.clipboard_monitor.set_last_content(content)

    # ===== 远程边缘检测 =====

    def _check_remote_edge(self):
        if not self.switch_controller or not self.switch_controller.target_screen:
            return False
        if time.time() * 1000 < self._switch_grace_until:
            return False

        target = self.switch_controller.target_screen
        direction = target.direction
        margin = self.RETURN_EDGE_MARGIN

        should_return = False
        if direction == 'left' and self._remote_x >= target.width - margin:
            should_return = True
        elif direction == 'right' and self._remote_x <= margin:
            should_return = True
        elif direction == 'top' and self._remote_y >= target.height - margin:
            should_return = True
        elif direction == 'bottom' and self._remote_y <= margin:
            should_return = True

        if should_return:
            print(f"[ShareServer] 虚拟光标到达远程边缘，返回本地。位置: ({self._remote_x}, {self._remote_y})")
            local_x, local_y = CoordinateMapper.map_to_local(
                target, self.switch_controller.current_screen,
                self._remote_x, self._remote_y
            )
            self.switch_controller.return_to_local(local_x, local_y)
            return True
        return False

    # ===== 事件分发 =====

    def _setup_dispatcher(self):
        self._dispatcher.register(MSG_TYPE_SWITCH, self._on_switch_from_client)
        self._dispatcher.register(MSG_TYPE_CLIPBOARD, self._on_clipboard_from_client)

    def _on_switch_from_client(self, target_x, target_y, action, screen_w=0, screen_h=0):
        pass

    def _on_edge_hit(self, direction):
        if self.switch_controller:
            self.switch_controller.on_edge_hit(direction)

    # ===== 切换控制器 =====

    def _init_switch_controller(self):
        if not self.layout_manager.get_local_screen():
            local_screen = ScreenLayout(
                screen_id="local",
                width=self._screen_width,
                height=self._screen_height,
                is_local=True
            )
            self.layout_manager.add_screen(local_screen)

        local_screen = self.layout_manager.get_local_screen()
        self.switch_controller = SwitchController(
            layout_manager=self.layout_manager,
            on_switch_to_remote=self._on_switch_to_remote,
            on_switch_to_local=self._on_switch_to_local,
            on_state_change=self._on_switch_state_change
        )
        self.switch_controller.set_local_screen(local_screen)

        self._screen_edge = ScreenEdge(
            on_edge_hit=self._on_edge_hit,
            threshold=10
        )
        print(f"[ShareServer] 切换控制器已初始化，本地屏幕: {local_screen.width}x{local_screen.height}")

    def _on_switch_to_remote(self, target_screen, mapped_x, mapped_y):
        print(f"[ShareServer] 切换到远程屏幕 {target_screen.screen_id}，坐标: ({mapped_x}, {mapped_y})")

        self._update_screen_size()
        hide_cursor()
        self._cursor_hidden = True

        self._remote_x = mapped_x
        self._remote_y = mapped_y
        self._remote_w = target_screen.width
        self._remote_h = target_screen.height

        self._switch_grace_until = time.time() * 1000 + 500

        if self.keyboard_listener:
            self.keyboard_listener.set_suppress(True)

        if _IS_WINDOWS and self._mouse_hook and self._mouse_hook._hook:
            self._mouse_hook.set_last_position(self._screen_center_x, self._screen_center_y)
            self._mouse_hook.set_active(True)
            ctypes.windll.user32.SetCursorPos(self._screen_center_x, self._screen_center_y)
            self.stop_mouse_listener()
        else:
            if self.mouse_listener:
                self.mouse_listener.suppress_next()
            self.mouse_controller.move_to(self._screen_center_x, self._screen_center_y)
            self._prev_x = self._screen_center_x
            self._prev_y = self._screen_center_y
            if self.mouse_listener:
                self.mouse_listener._last_x = self._screen_center_x
                self.mouse_listener._last_y = self._screen_center_y

        if self._client_socket:
            try:
                switch_data = pack_switch(mapped_x, mapped_y, 0, target_screen.width, target_screen.height)
                self._client_socket.sendall(switch_data)
                print(f"[ShareServer] 已发送切换命令 (屏幕: {target_screen.width}x{target_screen.height})")
            except Exception as e:
                print(f"[ShareServer] 发送切换命令失败: {e}")

    def _on_switch_to_local(self, x, y):
        print(f"[ShareServer] 返回本地屏幕，坐标: ({x}, {y})")
        self._switch_grace_until = time.time() * 1000 + 500

        if self.keyboard_listener:
            self.keyboard_listener.set_suppress(False)

        if _IS_WINDOWS and self._mouse_hook and self._mouse_hook._hook:
            self._mouse_hook.set_active(False)
            self.start_mouse_listener()

        if self._cursor_hidden:
            show_cursor()
            self._cursor_hidden = False
        self.mouse_controller.move_to(x, y)

    def _on_switch_state_change(self, new_state):
        print(f"[ShareServer] 切换状态变为: {new_state.value}")
        if new_state == SwitchState.NORMAL:
            if self.keyboard_listener:
                self.keyboard_listener.set_suppress(False)
            if _IS_WINDOWS and self._mouse_hook and self._mouse_hook._hook:
                self._mouse_hook.set_active(False)
                self.start_mouse_listener()
            if self._cursor_hidden:
                show_cursor()
                self._cursor_hidden = False

    def _reposition_cursor(self):
        if self.mouse_listener:
            self.mouse_listener.suppress_next()
        cx = self._screen_center_x
        cy = self._screen_center_y
        self.mouse_controller.move_to(cx, cy)
        self._prev_x = cx
        self._prev_y = cy
        if self.mouse_listener:
            self.mouse_listener._last_x = cx
            self.mouse_listener._last_y = cy

    def _send_to_client(self, data):
        if self._client_socket:
            try:
                self._client_socket.sendall(data)
            except Exception as e:
                print(f"[ShareServer] 发送数据失败: {e}")

    # ===== 远程屏幕管理 =====

    def add_remote_screen(self, screen_id, host, port, width, height, direction, alignment='left'):
        remote_screen = ScreenLayout(
            screen_id=screen_id,
            host=host,
            port=port,
            width=width,
            height=height,
            direction=direction,
            alignment=alignment,
            is_local=False
        )
        self.layout_manager.add_screen(remote_screen)
        if self.switch_controller:
            self.switch_controller.add_remote_screen(remote_screen)
        print(f"[ShareServer] 已添加远程屏幕: {screen_id} ({host}:{port})")

    # ===== 监听器管理 =====

    def start_mouse_listener(self):
        if self.mouse_listener is None:
            self.mouse_listener = MouseListener(on_mouse_event=self._on_mouse_event)
            self.mouse_listener.start()
            print("[ShareServer] 鼠标监听已启动")

    def stop_mouse_listener(self):
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
            print("[ShareServer] 鼠标监听已停止")

    def start_keyboard_listener(self):
        if self.keyboard_listener is None:
            self.keyboard_listener = KeyboardListener(on_keyboard_event=self._on_keyboard_event)
            self.keyboard_listener.start()
            print("[ShareServer] 键盘监听已启动")

    def stop_keyboard_listener(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            print("[ShareServer] 键盘监听已停止")

    def start_clipboard_monitor(self):
        if self.clipboard_monitor is None:
            self.clipboard_monitor = ClipboardMonitor(on_clipboard_change=self._on_clipboard_change)
            self.clipboard_monitor.start()
            print("[ShareServer] 剪贴板监控已启动")

    def stop_clipboard_monitor(self):
        if self.clipboard_monitor:
            self.clipboard_monitor.stop()
            self.clipboard_monitor = None
            print("[ShareServer] 剪贴板监控已停止")

    def start_all_listeners(self):
        self.start_mouse_listener()
        self.start_keyboard_listener()
        self.start_clipboard_monitor()
        if _IS_WINDOWS and self._mouse_hook is None:
            self._mouse_hook = MouseHook(
                on_move=self._on_hook_move,
                on_button=self._on_hook_button,
                on_scroll=self._on_hook_scroll
            )
            self._mouse_hook.install()
            self._mouse_hook.set_active(False)
            print("[ShareServer] Windows 鼠标钩子已安装")

    def stop_all_listeners(self):
        self.stop_mouse_listener()
        self.stop_keyboard_listener()
        self.stop_clipboard_monitor()
        if _IS_WINDOWS and self._mouse_hook:
            self._mouse_hook.set_active(False)
            self._mouse_hook.uninstall()
            self._mouse_hook = None
            print("[ShareServer] Windows 鼠标钩子已卸载")

    # ===== 客户端连接处理 =====

    def _handle_client(self, client_socket, client_addr):
        self._client_socket = client_socket
        self._client_addr = client_addr
        print(f"[ShareServer] 客户端已连接: {client_addr}")
        self.start_all_listeners()
        try:
            while self.running and self._client_socket:
                client_socket.settimeout(0.5)
                try:
                    data = client_socket.recv(8192)
                    if not data:
                        break
                    self._dispatcher.dispatch(data)
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"[ShareServer] 接收数据错误: {e}")
        finally:
            self.stop_all_listeners()
            if self._cursor_hidden:
                show_cursor()
                self._cursor_hidden = False
            if self.keyboard_listener:
                self.keyboard_listener.set_suppress(False)
            try:
                client_socket.close()
            except:
                pass
            self._client_socket = None
            self._client_addr = None
            print(f"[ShareServer] 客户端断开: {client_addr}")

    def start(self):
        super().start()

    def stop(self):
        self.stop_all_listeners()
        if self._cursor_hidden:
            show_cursor()
            self._cursor_hidden = False
        if self.keyboard_listener:
            self.keyboard_listener.set_suppress(False)
        super().stop()