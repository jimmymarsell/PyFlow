import threading
import time
import pyautogui
from common.system_utils import get_screen_size

EDGE_THRESHOLD = 5

class ScreenEdge:
    """
    屏幕边缘检测器
    检测鼠标是否接近屏幕边缘，触发切换提示
    """
    def __init__(self, on_edge_hit=None, on_mouse_move=None, threshold=EDGE_THRESHOLD):
        """
        初始化屏幕边缘检测器
        :param on_edge_hit: 边缘命中回调函数，接收边缘方向参数 ('left', 'right', 'top', 'bottom')
        :param on_mouse_move: 鼠标移动回调函数，接收 (x, y) 坐标参数
        :param threshold: 边缘阈值（像素）
        """
        self.on_edge_hit = on_edge_hit
        self.on_mouse_move = on_mouse_move
        self.threshold = threshold
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._screen_width = 0
        self._screen_height = 0

    def start(self):
        """
        启动边缘检测
        """
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._update_screen_size()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """
        停止边缘检测
        """
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _update_screen_size(self):
        """
        更新屏幕尺寸
        """
        width, height = get_screen_size()
        self._screen_width = width
        self._screen_height = height

    def _monitor_loop(self):
        """
        监控循环
        定期检查鼠标位置是否接近边缘
        """
        while not self._stop_event.is_set():
            try:
                x, y = pyautogui.position()
                self._check_edges(x, y)
            except Exception:
                pass
            self._stop_event.wait(0.05)

    def _check_edges(self, x, y):
        """
        检查是否触及边缘
        :param x: 鼠标X坐标
        :param y: 鼠标Y坐标
        """
        if self.on_mouse_move:
            self.on_mouse_move(x, y)

        if x <= self.threshold and self.on_edge_hit:
            self.on_edge_hit('left')
        elif x >= self._screen_width - self.threshold and self.on_edge_hit:
            self.on_edge_hit('right')
        if y <= self.threshold and self.on_edge_hit:
            self.on_edge_hit('top')
        elif y >= self._screen_height - self.threshold and self.on_edge_hit:
            self.on_edge_hit('bottom')
