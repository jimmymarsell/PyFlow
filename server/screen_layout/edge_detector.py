"""
边界检测器

检测鼠标是否到达屏幕边界，触发屏幕切换
"""

from typing import Optional, Callable
from .screen_layout import ScreenLayout


class EdgeDetector:
    """
    屏幕边界检测器

    负责检测鼠标是否到达屏幕边界，决定是否触发屏幕切换

    使用方式：
    1. 初始化时指定目标屏幕和边缘触发回调
    2. 每次鼠标移动时调用 check() 方法
    3. 当鼠标到达边界时触发回调
    """

    def __init__(
        self,
        target_screen: ScreenLayout,
        on_edge_reached: Optional[Callable[['EdgeDetector', str, int, int], None]] = None
    ):
        """
        初始化边界检测器

        Args:
            target_screen: 目标屏幕配置
            on_edge_reached: 到达边界时的回调函数 (detector, direction, x, y)
        """
        self.target_screen = target_screen
        self.on_edge_reached = on_edge_reached
        self.edge_margin = target_screen.edge_margin
        self.direction = target_screen.direction
        self.width = target_screen.width
        self.height = target_screen.height

    def set_edge_margin(self, margin: int) -> None:
        """设置边缘触发阈值"""
        self.edge_margin = margin

    def is_at_edge(self, x: int, y: int) -> bool:
        """
        检测鼠标是否在切换边界上

        Args:
            x: 鼠标X坐标
            y: 鼠标Y坐标

        Returns:
            True if mouse is at edge, False otherwise
        """
        margin = self.edge_margin

        if self.direction == 'left':
            return x <= margin
        elif self.direction == 'right':
            return x >= self.width - margin
        elif self.direction == 'top':
            return y <= margin
        elif self.direction == 'bottom':
            return y >= self.height - margin

        return False

    def get_edge_direction(self, x: int, y: int) -> Optional[str]:
        """
        获取鼠标所在的边界方向

        Returns:
            'left', 'right', 'top', 'bottom' 或 None
        """
        margin = self.edge_margin

        if x <= margin:
            return 'left'
        elif x >= self.width - margin:
            return 'right'
        elif y <= margin:
            return 'top'
        elif y >= self.height - margin:
            return 'bottom'

        return None

    def check(self, x: int, y: int) -> bool:
        """
        检查鼠标位置，决定是否触发切换

        Args:
            x: 鼠标X坐标
            y: 鼠标Y坐标

        Returns:
            True if switch should be triggered, False otherwise
        """
        if self.is_at_edge(x, y):
            if self.on_edge_reached:
                self.on_edge_reached(self, self.direction, x, y)
            return True
        return False

    def is_moving_toward_edge(self, x: int, y: int, prev_x: int, prev_y: int) -> bool:
        """
        检测鼠标是否正在向边界方向移动

        Args:
            x: 当前X坐标
            y: 当前Y坐标
            prev_x: 上次X坐标
            prev_y: 上次Y坐标

        Returns:
            True if moving toward edge, False otherwise
        """
        if self.direction == 'left':
            return x < prev_x and x <= self.edge_margin
        elif self.direction == 'right':
            return x > prev_x and x >= self.width - self.edge_margin
        elif self.direction == 'top':
            return y < prev_y and y <= self.edge_margin
        elif self.direction == 'bottom':
            return y > prev_y and y >= self.height - self.edge_margin
        return False

    def get_edge_position(self) -> tuple:
        """
        获取边界位置坐标

        用于计算切换后鼠标应该出现的位置

        Returns:
            (x, y) 边界位置坐标
        """
        margin = self.edge_margin

        if self.direction == 'left':
            return (0, 0)
        elif self.direction == 'right':
            return (self.width - 1, 0)
        elif self.direction == 'top':
            return (0, 0)
        elif self.direction == 'bottom':
            return (0, self.height - 1)

        return (0, 0)
