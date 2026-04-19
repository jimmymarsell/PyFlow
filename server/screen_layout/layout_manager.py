"""
布局管理器

管理所有屏幕的布局配置，提供屏幕查询和坐标计算功能
"""

import json
from typing import Optional, Dict, List
from .screen_layout import ScreenLayout


class LayoutManager:
    """
    布局管理器

    负责：
    - 加载和管理布局配置
    - 维护屏幕列表
    - 提供屏幕查询接口
    - 计算虚拟屏幕坐标
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化布局管理器

        Args:
            config_path: 布局配置文件路径（JSON格式）
        """
        self.screens: Dict[str, ScreenLayout] = {}
        self.local_screen: Optional[ScreenLayout] = None
        self.remote_screens: Dict[str, ScreenLayout] = {}

        if config_path:
            try:
                self.load_config(config_path)
            except FileNotFoundError:
                print(f"[LayoutManager] 配置文件不存在: {config_path}")

    def add_screen(self, screen: ScreenLayout) -> None:
        """
        添加屏幕到布局

        Args:
            screen: 屏幕布局配置
        """
        self.screens[screen.screen_id] = screen

        if screen.is_local:
            self.local_screen = screen
        else:
            self.remote_screens[screen.screen_id] = screen

    def get_screen(self, screen_id: str) -> Optional[ScreenLayout]:
        """根据 ID 获取屏幕"""
        return self.screens.get(screen_id)

    def get_local_screen(self) -> Optional[ScreenLayout]:
        """获取本地屏幕"""
        return self.local_screen

    def get_all_screens(self) -> List[ScreenLayout]:
        """获取所有屏幕"""
        return list(self.screens.values())

    def get_remote_screens(self) -> List[ScreenLayout]:
        """获取所有远程屏幕"""
        return list(self.remote_screens.values())

    def get_screen_at(self, x: int, y: int) -> Optional[ScreenLayout]:
        """
        根据坐标查找对应屏幕

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            包含该坐标的屏幕，如果没有则返回 None
        """
        for screen in self.screens.values():
            if screen.contains_point(x, y):
                return screen
        return None

    def get_screen_by_direction(self, direction: str) -> Optional[ScreenLayout]:
        """
        根据方向查找远程屏幕

        Args:
            direction: 方向 ('left', 'right', 'top', 'bottom')

        Returns:
            该方向的远程屏幕，如果没有则返回 None
        """
        return self.remote_screens.get(direction)

    def get_adjacent_screen(self, from_screen: ScreenLayout, direction: str) -> Optional[ScreenLayout]:
        """
        获取指定方向相邻的屏幕

        Args:
            from_screen: 源屏幕
            direction: 方向 ('left', 'right', 'top', 'bottom')

        Returns:
            相邻屏幕，如果没有则返回 None
        """
        for screen in self.remote_screens.values():
            if screen.direction == direction:
                return screen
        return None

    def get_opposite_direction(self, direction: str) -> str:
        """获取相反方向"""
        opposites = {
            'left': 'right',
            'right': 'left',
            'top': 'bottom',
            'bottom': 'top',
        }
        return opposites.get(direction, '')

    def calculate_virtual_position(self, screen: ScreenLayout, x: int, y: int) -> tuple:
        """
        计算在虚拟屏幕中的绝对坐标

        Args:
            screen: 屏幕
            x: 屏幕内相对X坐标
            y: 屏幕内相对Y坐标

        Returns:
            (虚拟X坐标, 虚拟Y坐标)
        """
        offset = screen.get_offset()
        return (x + offset['x'], y + offset['y'])

    def load_config(self, config_path: str) -> None:
        """
        从文件加载布局配置

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        version = config.get('version', 1)

        if version == 1:
            self._load_v1_config(config)
        else:
            raise ValueError(f"不支持的配置文件版本: {version}")

    def _load_v1_config(self, config: dict) -> None:
        """加载 V1 版本配置"""
        screens_config = config.get('screens', [])
        for screen_data in screens_config:
            screen = ScreenLayout.from_dict(screen_data)
            self.add_screen(screen)

    def save_config(self, config_path: str) -> None:
        """
        保存布局配置到文件

        Args:
            config_path: 配置文件路径
        """
        screens_list = []
        for screen in self.screens.values():
            screens_list.append(screen.to_dict())

        config = {
            'version': 1,
            'screens': screens_list,
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def get_config_dict(self) -> dict:
        """获取配置字典（用于内存中使用）"""
        screens_list = []
        for screen in self.screens.values():
            screens_list.append(screen.to_dict())

        return {
            'version': 1,
            'screens': screens_list,
        }
