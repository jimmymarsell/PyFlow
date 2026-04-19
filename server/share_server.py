import threading
import socket
from network.tcp_server import TCPServer
from client.mouse_controller import MouseController
from server.mouse_listener import MouseListener
from server.keyboard_listener import KeyboardListener
from server.clipboard_monitor import ClipboardMonitor
from server.screen_edge import ScreenEdge
from server.screen_layout import ScreenLayout, LayoutManager, EdgeDetector, CoordinateMapper, SwitchController, SwitchState
from common.event_dispatcher import EventDispatcher
from common.protocol import (
    pack_switch,
    MSG_TYPE_MOUSE_MOVE,
    MSG_TYPE_MOUSE_BUTTON,
    MSG_TYPE_MOUSE_SCROLL,
    MSG_TYPE_KEYBOARD,
    MSG_TYPE_CLIPBOARD,
    MSG_TYPE_SWITCH
)

class ShareServer(TCPServer):
    """
    共享服务端（主控端）
    监听本地鼠标/键盘事件并发送到被控端
    继承自 TCPServer，复用基础 TCP 连接能力

    架构说明：
    - Server（主控端）：监听本地鼠标/键盘，将事件发送到 Client
    - Client（被控端）：接收事件，在本地执行鼠标/键盘操作
    """
    def __init__(self, host="0.0.0.0", port=12345, config_path=None):
        """
        初始化共享服务端
        :param host: 监听地址
        :param port: 监听端口
        :param config_path: 屏幕布局配置文件路径
        """
        super().__init__(host, port)
        self.mouse_controller = MouseController()
        self.mouse_listener = None
        self.keyboard_listener = None
        self.clipboard_monitor = None
        self.screen_edge = None
        self._client_socket = None
        self._client_addr = None

        self.layout_manager = LayoutManager(config_path)
        self.switch_controller = None
        self._dispatcher = EventDispatcher()
        self._setup_dispatcher()
        self._init_switch_controller()

    def _on_mouse_event(self, data):
        """
        处理本地鼠标事件
        将本地鼠标事件发送到已连接的客户端
        :param data: 鼠标事件字节数据
        """
        if self.switch_controller and self.switch_controller.is_remote_control():
            return

        if self._client_socket:
            try:
                self._client_socket.sendall(data)
            except Exception as e:
                print(f"[ShareServer] 发送鼠标事件失败: {e}")

    def _on_keyboard_event(self, data):
        """
        处理本地键盘事件
        将本地键盘事件发送到已连接的客户端
        :param data: 键盘事件字节数据
        """
        if self._client_socket:
            try:
                self._client_socket.sendall(data)
            except Exception as e:
                print(f"[ShareServer] 发送键盘事件失败: {e}")

    def _on_clipboard_change(self, data):
        """
        处理剪贴板变化
        将剪贴板内容发送到已连接的客户端
        :param data: 剪贴板事件字节数据
        """
        if self._client_socket:
            try:
                self._client_socket.sendall(data)
            except Exception as e:
                print(f"[ShareServer] 发送剪贴板事件失败: {e}")

    def _setup_dispatcher(self):
        """
        设置事件分发器
        """
        self._dispatcher.register(MSG_TYPE_SWITCH, self._on_switch_from_client)

    def _on_switch_from_client(self, target_x, target_y, action):
        """
        处理来自客户端的切换返回命令
        """
        if action == 1:
            print(f"[ShareServer] 收到客户端返回请求，坐标: ({target_x}, {target_y})")
            if self.switch_controller:
                self.switch_controller.return_to_local(target_x, target_y)

    def _on_edge_hit(self, direction):
        """
        处理屏幕边缘命中
        :param direction: 边缘方向 ('left', 'right', 'top', 'bottom')
        """
        if self.switch_controller:
            self.switch_controller.on_edge_hit(direction)

    def _init_switch_controller(self):
        """
        初始化切换控制器
        """
        if not self.layout_manager.get_local_screen():
            local_screen = ScreenLayout(
                screen_id="local",
                width=1920,
                height=1080,
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
        """
        切换到远程屏幕
        :param target_screen: 目标屏幕
        :param mapped_x: 映射后的X坐标
        :param mapped_y: 映射后的Y坐标
        """
        print(f"[ShareServer] 切换到远程屏幕 {target_screen.screen_id}，坐标: ({mapped_x}, {mapped_y})")
        if self._client_socket:
            try:
                switch_data = pack_switch(mapped_x, mapped_y, 0)
                self._client_socket.sendall(switch_data)
                print(f"[ShareServer] 已发送切换命令到客户端")
            except Exception as e:
                print(f"[ShareServer] 发送切换命令失败: {e}")

    def _on_switch_to_local(self, x, y):
        """
        返回本地屏幕
        :param x: X坐标
        :param y: Y坐标
        """
        print(f"[ShareServer] 返回本地屏幕，坐标: ({x}, {y})")
        self.mouse_controller.move_to(x, y)

    def _on_switch_state_change(self, new_state):
        """
        切换状态变化
        :param new_state: 新状态
        """
        print(f"[ShareServer] 切换状态变为: {new_state.value}")

    def add_remote_screen(self, screen_id, host, port, width, height, direction, alignment='left'):
        """
        添加远程屏幕配置
        :param screen_id: 屏幕ID
        :param host: 远程主机IP
        :param port: 远程主机端口
        :param width: 屏幕宽度
        :param height: 屏幕高度
        :param direction: 拼接方向
        :param alignment: 对齐方式
        """
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

    def on_mouse_move(self, x, y):
        """
        处理鼠标移动（供外部调用，用于边缘检测）
        :param x: 鼠标X坐标
        :param y: 鼠标Y坐标
        """
        if self.switch_controller:
            self.switch_controller.on_mouse_move(x, y)

    def start_mouse_listener(self):
        """
        启动鼠标监听器
        """
        if self.mouse_listener is None:
            self.mouse_listener = MouseListener(on_mouse_event=self._on_mouse_event)
            self.mouse_listener.start()
            print("[ShareServer] 鼠标监听已启动")

    def stop_mouse_listener(self):
        """
        停止鼠标监听器
        """
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
            print("[ShareServer] 鼠标监听已停止")

    def start_keyboard_listener(self):
        """
        启动键盘监听器
        """
        if self.keyboard_listener is None:
            self.keyboard_listener = KeyboardListener(on_keyboard_event=self._on_keyboard_event)
            self.keyboard_listener.start()
            print("[ShareServer] 键盘监听已启动")

    def stop_keyboard_listener(self):
        """
        停止键盘监听器
        """
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            print("[ShareServer] 键盘监听已停止")

    def start_clipboard_monitor(self):
        """
        启动剪贴板监控
        """
        if self.clipboard_monitor is None:
            self.clipboard_monitor = ClipboardMonitor(on_clipboard_change=self._on_clipboard_change)
            self.clipboard_monitor.start()
            print("[ShareServer] 剪贴板监控已启动")

    def stop_clipboard_monitor(self):
        """
        停止剪贴板监控
        """
        if self.clipboard_monitor:
            self.clipboard_monitor.stop()
            self.clipboard_monitor = None
            print("[ShareServer] 剪贴板监控已停止")

    def start_screen_edge(self):
        """
        启动屏幕边缘检测
        """
        if self._screen_edge is None:
            self._screen_edge = ScreenEdge(
                on_edge_hit=self._on_edge_hit,
                on_mouse_move=self.on_mouse_move
            )
        self._screen_edge.start()
        print("[ShareServer] 屏幕边缘检测已启动")

    def stop_screen_edge(self):
        """
        停止屏幕边缘检测
        """
        if self._screen_edge:
            self._screen_edge.stop()
            self._screen_edge = None
            print("[ShareServer] 屏幕边缘检测已停止")

    def start_all_listeners(self):
        """
        启动所有监听器
        """
        self.start_mouse_listener()
        self.start_keyboard_listener()
        self.start_clipboard_monitor()
        self.start_screen_edge()

    def stop_all_listeners(self):
        """
        停止所有监听器
        """
        self.stop_mouse_listener()
        self.stop_keyboard_listener()
        self.stop_clipboard_monitor()
        self.stop_screen_edge()

    def _handle_client(self, client_socket, client_addr):
        """
        处理客户端连接
        :param client_socket: 客户端 socket
        :param client_addr: 客户端地址
        """
        self._client_socket = client_socket
        self._client_addr = client_addr
        print(f"[ShareServer] 客户端已连接: {client_addr}")
        self.start_all_listeners()
        try:
            while self.running and self._client_socket:
                client_socket.settimeout(0.5)
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    self._dispatcher.dispatch(data)
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"[ShareServer] 接收数据错误: {e}")
        finally:
            self.stop_all_listeners()
            try:
                client_socket.close()
            except:
                pass
            self._client_socket = None
            self._client_addr = None
            print(f"[ShareServer] 客户端断开: {client_addr}")

    def start(self):
        """
        启动服务端
        """
        super().start()

    def stop(self):
        """
        停止服务端
        """
        self.stop_all_listeners()
        super().stop()
