"""
切换控制器

管理屏幕间切换逻辑的状态机
"""

from typing import Optional, Callable
from enum import Enum
from .screen_layout import ScreenLayout
from .layout_manager import LayoutManager
from .edge_detector import EdgeDetector
from .coordinate_mapper import CoordinateMapper


class SwitchState(Enum):
    """切换状态枚举"""
    NORMAL = "normal"
    SWITCHING = "switching"
    REMOTE = "remote"
    RETURNING = "returning"


class SwitchAction(Enum):
    """切换动作枚举"""
    TO_REMOTE = 0
    TO_LOCAL = 1


class SwitchController:
    """
    切换控制器

    负责：
    - 管理切换状态机
    - 检测边界并触发切换
    - 计算切换后的坐标
    - 协调本地和远程鼠标控制

    状态转换：
    NORMAL → SWITCHING (鼠标到达边界)
    SWITCHING → REMOTE (切换完成)
    REMOTE → RETURNING (鼠标到达远程边界)
    RETURNING → NORMAL (返回完成)
    """

    def __init__(
        self,
        layout_manager: LayoutManager,
        on_switch_to_remote: Optional[Callable[[ScreenLayout, int, int], None]] = None,
        on_switch_to_local: Optional[Callable[[int, int], None]] = None,
        on_state_change: Optional[Callable[[SwitchState], None]] = None
    ):
        """
        初始化切换控制器

        Args:
            layout_manager: 布局管理器
            on_switch_to_remote: 切换到远程屏幕时的回调 (screen, x, y)
            on_switch_to_local: 返回本地屏幕时的回调 (x, y)
            on_state_change: 状态变化时的回调 (new_state)
        """
        self.layout_manager = layout_manager
        self.on_switch_to_remote = on_switch_to_remote
        self.on_switch_to_local = on_switch_to_local
        self.on_state_change = on_state_change

        self.state = SwitchState.NORMAL
        self.current_screen: Optional[ScreenLayout] = None
        self.target_screen: Optional[ScreenLayout] = None
        self.edge_detectors: dict[str, EdgeDetector] = {}
        self._prev_x = 0
        self._prev_y = 0
        self._last_switch_time = 0
        self._switch_cooldown_ms = 200

        self._init_edge_detectors()

    def _init_edge_detectors(self):
        """初始化所有远程屏幕的边界检测器"""
        for screen in self.layout_manager.get_remote_screens():
            detector = EdgeDetector(
                target_screen=screen,
                on_edge_reached=self._on_edge_reached
            )
            self.edge_detectors[screen.screen_id] = detector

    def _on_edge_reached(self, detector: EdgeDetector, direction: str, x: int, y: int):
        """边界到达回调"""
        self.switch_to_remote(detector.target_screen, x, y)

    def on_edge_hit(self, direction: str):
        """
        处理边缘命中事件（由 ScreenEdge 调用）
        :param direction: 边缘方向 ('left', 'right', 'top', 'bottom')
        """
        if self.state != SwitchState.NORMAL:
            return

        if not self.current_screen:
            return

        remote_screen = self.layout_manager.get_adjacent_screen(self.current_screen, direction)
        if not remote_screen:
            return

        width = self.current_screen.width
        height = self.current_screen.height

        x = 0
        y = height // 2
        if direction == 'right':
            x = width - 1
        elif direction == 'left':
            x = 0
        elif direction == 'bottom':
            x = width // 2
            y = height - 1
        elif direction == 'top':
            x = width // 2
            y = 0

        self.switch_to_remote(remote_screen, x, y)

    def _change_state(self, new_state: SwitchState):
        """状态变化处理"""
        if self.state != new_state:
            self.state = new_state
            if self.on_state_change:
                self.on_state_change(new_state)

    def get_state(self) -> SwitchState:
        """获取当前状态"""
        return self.state

    def set_local_screen(self, screen: ScreenLayout):
        """设置本地屏幕"""
        self.current_screen = screen

    def on_mouse_move(self, x: int, y: int):
        """
        处理鼠标移动事件

        Args:
            x: 鼠标X坐标
            y: 鼠标Y坐标
        """
        self._prev_x = x
        self._prev_y = y

        if self.state == SwitchState.NORMAL:
            self._check_boundary(x, y)
        elif self.state == SwitchState.REMOTE:
            self._check_remote_boundary(x, y)

    def _check_boundary(self, x: int, y: int):
        """检查是否到达边界"""
        for detector in self.edge_detectors.values():
            if detector.check(x, y):
                break

    def _check_remote_boundary(self, x: int, y: int):
        """检查远程屏幕边界（用于返回）"""
        if not self.current_screen:
            return

        margin = self.current_screen.edge_margin
        width = self.current_screen.width
        height = self.current_screen.height

        at_boundary = False
        direction = None

        if x <= margin:
            at_boundary = True
            direction = 'left'
        elif x >= width - margin:
            at_boundary = True
            direction = 'right'
        elif y <= margin:
            at_boundary = True
            direction = 'top'
        elif y >= height - margin:
            at_boundary = True
            direction = 'bottom'

        if at_boundary and direction:
            mapped_x, mapped_y = self._map_to_local(x, y)
            self.return_to_local(mapped_x, mapped_y)

    def switch_to_remote(self, target_screen: ScreenLayout, x: int, y: int):
        """
        切换到远程屏幕

        Args:
            target_screen: 目标屏幕
            x: 当前X坐标
            y: 当前Y坐标
        """
        if self.state != SwitchState.NORMAL:
            return

        self._change_state(SwitchState.SWITCHING)
        self.target_screen = target_screen

        mapped_x, mapped_y = self._map_to_remote(x, y)

        if self.on_switch_to_remote:
            self.on_switch_to_remote(target_screen, mapped_x, mapped_y)

        self._change_state(SwitchState.REMOTE)

    def return_to_local(self, x: int, y: int):
        """
        返回本地屏幕

        Args:
            x: 目标X坐标
            y: 目标Y坐标
        """
        if self.state != SwitchState.REMOTE:
            return

        self._change_state(SwitchState.RETURNING)

        if self.on_switch_to_local:
            self.on_switch_to_local(x, y)

        self._change_state(SwitchState.NORMAL)

    def _map_to_remote(self, x: int, y: int) -> tuple[int, int]:
        """
        将坐标映射到远程屏幕

        Args:
            x: 本地屏幕X坐标
            y: 本地屏幕Y坐标

        Returns:
            (远程屏幕X坐标, 远程屏幕Y坐标)
        """
        if not self.target_screen or not self.current_screen:
            return (0, 0)

        return CoordinateMapper.map_to_remote(
            self.current_screen,
            self.target_screen,
            x, y
        )

    def _map_to_local(self, x: int, y: int) -> tuple[int, int]:
        """
        将坐标映射到本地屏幕

        Args:
            x: 远程屏幕X坐标
            y: 远程屏幕Y坐标

        Returns:
            (本地屏幕X坐标, 本地屏幕Y坐标)
        """
        if not self.current_screen or not self.target_screen:
            return (0, 0)

        return CoordinateMapper.map_to_local(
            self.target_screen,
            self.current_screen,
            x, y
        )

    def is_remote_control(self) -> bool:
        """是否正在控制远程屏幕"""
        return self.state == SwitchState.REMOTE

    def reset(self):
        """重置控制器到初始状态"""
        self._change_state(SwitchState.NORMAL)
        self.target_screen = None

    def add_remote_screen(self, screen: ScreenLayout):
        """
        添加远程屏幕并初始化其边缘检测器
        :param screen: 远程屏幕
        """
        if screen.screen_id not in self.edge_detectors:
            detector = EdgeDetector(
                target_screen=screen,
                on_edge_reached=self._on_edge_reached
            )
            self.edge_detectors[screen.screen_id] = detector
            print(f"[SwitchController] 已添加远程屏幕边缘检测器: {screen.screen_id}")
