import threading
import time

class Reconnect:
    """
    自动重连器
    监听连接状态，断开后自动重连
    """
    def __init__(self, connect_func, on_reconnecting=None,
                 max_retries=-1, initial_delay=1.0, max_delay=30.0, backoff_factor=1.5):
        """
        初始化自动重连器
        :param connect_func: 连接函数，调用时尝试建立连接，返回 True 表示成功
        :param on_reconnecting: 重连中回调函数，接收 (attempt, delay) 参数
        :param max_retries: 最大重试次数，-1 表示无限重试
        :param initial_delay: 初始重试延迟（秒）
        :param max_delay: 最大重试延迟（秒）
        :param backoff_factor: 退避因子
        """
        self.connect_func = connect_func
        self.on_reconnecting = on_reconnecting
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._retry_count = 0
        self._current_delay = initial_delay

    def start(self):
        """
        启动自动重连
        """
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._retry_count = 0
        self._current_delay = self.initial_delay
        self._thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """
        停止自动重连
        """
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _reconnect_loop(self):
        """
        重连循环
        """
        while not self._stop_event.is_set():
            if self.connect_func():
                self._retry_count = 0
                self._current_delay = self.initial_delay
                self._stop_event.wait(1.0)
            else:
                if self.max_retries != -1 and self._retry_count >= self.max_retries:
                    break

                self._retry_count += 1
                if self.on_reconnecting:
                    self.on_reconnecting(self._retry_count, self._current_delay)

                self._stop_event.wait(self._current_delay)
                self._current_delay = min(self._current_delay * self.backoff_factor, self.max_delay)

    def get_retry_count(self):
        """
        获取当前重试次数
        :return: 重试次数
        """
        return self._retry_count

    def reset_delay(self):
        """
        重置延迟到初始值
        """
        self._current_delay = self.initial_delay
