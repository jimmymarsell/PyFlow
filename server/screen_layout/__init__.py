"""
屏幕拼接布局模块

提供多屏幕拼接模式的核心功能：
- ScreenLayout: 屏幕布局配置数据类
- LayoutManager: 布局管理器
- EdgeDetector: 边界检测器
- CoordinateMapper: 坐标映射器
- SwitchController: 切换控制器
- SwitchState: 切换状态枚举
- SwitchAction: 切换动作枚举
"""

from .screen_layout import ScreenLayout
from .layout_manager import LayoutManager
from .edge_detector import EdgeDetector
from .coordinate_mapper import CoordinateMapper
from .switch_controller import SwitchController, SwitchState, SwitchAction

__all__ = [
    'ScreenLayout',
    'LayoutManager',
    'EdgeDetector',
    'CoordinateMapper',
    'SwitchController',
    'SwitchState',
    'SwitchAction',
]

__version__ = '1.0.0'