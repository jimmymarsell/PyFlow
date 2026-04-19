import time
import threading
import pyperclip
from common.protocol import pack_clipboard

class ClipboardMonitor:
    """
    剪贴板监控器
    监控本地剪贴板变化并发送通知
    """
    def __init__(self, on_clipboard_change=None, poll_interval=0.5):
        """
        初始化剪贴板监控器
        :param on_clipboard_change: 剪贴板变化回调函数，接收字节数据参数
        :param poll_interval: 轮询间隔（秒）
        """
        self.on_clipboard_change = on_clipboard_change
        self.poll_interval = poll_interval
        self._last_content = ""
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """
        启动剪贴板监控
        """
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """
        停止剪贴板监控
        """
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _monitor_loop(self):
        """
        监控循环
        定期检查剪贴板内容是否变化
        """
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
        """
        获取当前剪贴板内容
        :return: 剪贴板文本内容
        """
        try:
            return pyperclip.paste()
        except Exception:
            return ""
