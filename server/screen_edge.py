import time
from common.system_utils import get_screen_size

EDGE_THRESHOLD = 5


class ScreenEdge:
    """
    屏幕边缘检测器（事件驱动版）

    不再使用轮询，而是由 MouseListener 的事件回调驱动。
    通过 update(x, y) 方法接收实时鼠标位置。
    """
    def __init__(self, on_edge_hit=None, threshold=EDGE_THRESHOLD):
        self.on_edge_hit = on_edge_hit
        self.threshold = threshold
        self._screen_width = 0
        self._screen_height = 0
        self._last_edge_time = 0
        self._cooldown = 0.15
        self._last_direction = None
        self._hit_count = 0
        self._hit_threshold = 2

    def start(self):
        self._update_screen_size()

    def stop(self):
        pass

    def _update_screen_size(self):
        width, height = get_screen_size()
        self._screen_width = width
        self._screen_height = height

    def update(self, x, y):
        """
        事件驱动：由外部（如 MouseListener 回调）调用，传入实时鼠标位置。
        替代原来的轮询 _monitor_loop。
        """
        self._check_edges(x, y)

    def _check_edges(self, x, y):
        current_time = time.time()
        if current_time - self._last_edge_time < self._cooldown:
            return

        direction = None
        if x <= self.threshold:
            direction = 'left'
        elif x >= self._screen_width - self.threshold:
            direction = 'right'
        elif y <= self.threshold:
            direction = 'top'
        elif y >= self._screen_height - self.threshold:
            direction = 'bottom'

        if direction and self.on_edge_hit:
            self._last_edge_time = current_time
            self.on_edge_hit(direction)