"""
坐标映射器

实现不同分辨率屏幕间的坐标映射计算
"""

from typing import Tuple
from .screen_layout import ScreenLayout


class CoordinateMapper:
    """
    坐标映射器

    负责在不同屏幕之间进行坐标映射，考虑：
    - 屏幕对齐方式（左对齐、右对齐、上对齐、下对齐）
    - 分辨率比例
    - 偏移量微调
    """

    @staticmethod
    def map_to_remote(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        将坐标从源屏幕映射到目标（远程）屏幕

        Args:
            from_screen: 源屏幕配置
            to_screen: 目标屏幕配置
            x: 源屏幕上的X坐标
            y: 源屏幕上的Y坐标

        Returns:
            (目标屏幕X坐标, 目标屏幕Y坐标)
        """
        if to_screen.direction == 'left':
            return CoordinateMapper._map_from_right(from_screen, to_screen, x, y)
        elif to_screen.direction == 'right':
            return CoordinateMapper._map_from_left(from_screen, to_screen, x, y)
        elif to_screen.direction == 'top':
            return CoordinateMapper._map_from_bottom(from_screen, to_screen, x, y)
        elif to_screen.direction == 'bottom':
            return CoordinateMapper._map_from_top(from_screen, to_screen, x, y)

        return (0, 0)

    @staticmethod
    def _map_from_right(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从源屏幕右边界映射到目标屏幕左边界

        左对齐：
        源屏幕右边界 → 目标屏幕左边界

        映射逻辑：
        - x: 从源屏幕右边界（比例映射）→ 目标屏幕左边界
        - y: 按高度比例映射
        """
        ratio_x = x / from_screen.width
        ratio_y = y / from_screen.height

        if to_screen.alignment == 'left':
            new_x = 0
        elif to_screen.alignment == 'right':
            new_x = to_screen.width - int(ratio_x * to_screen.width)
        elif to_screen.alignment == 'center':
            new_x = int((to_screen.width - ratio_x * to_screen.width) / 2)
        else:
            new_x = 0

        new_y = int(ratio_y * to_screen.height)

        return (new_x + to_screen.offset_x, new_y + to_screen.offset_y)

    @staticmethod
    def _map_from_left(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从源屏幕左边界映射到目标屏幕右边界

        右对齐：
        源屏幕左边界 → 目标屏幕右边界

        映射逻辑：
        - x: 从源屏幕左边界（比例映射）→ 目标屏幕右边界
        - y: 按高度比例映射
        """
        ratio_x = x / from_screen.width
        ratio_y = y / from_screen.height

        if to_screen.alignment == 'right':
            new_x = to_screen.width - 1
        elif to_screen.alignment == 'left':
            new_x = to_screen.width - int((1 - ratio_x) * to_screen.width)
        elif to_screen.alignment == 'center':
            new_x = int((to_screen.width + ratio_x * to_screen.width) / 2)
        else:
            new_x = to_screen.width - 1

        new_y = int(ratio_y * to_screen.height)

        return (new_x + to_screen.offset_x, new_y + to_screen.offset_y)

    @staticmethod
    def _map_from_bottom(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从源屏幕下边界映射到目标屏幕上边界

        上对齐：
        源屏幕下边界 → 目标屏幕上边界

        映射逻辑：
        - x: 按宽度比例映射
        - y: 从源屏幕下边界（比例映射）→ 目标屏幕上边界
        """
        ratio_x = x / from_screen.width
        ratio_y = y / from_screen.height

        new_x = int(ratio_x * to_screen.width)
        new_y = 0

        if to_screen.alignment == 'top':
            new_y = 0
        elif to_screen.alignment == 'bottom':
            new_y = to_screen.height - int((1 - ratio_y) * to_screen.height)
        elif to_screen.alignment == 'center':
            new_y = int((to_screen.height - ratio_y * to_screen.height) / 2)

        return (new_x + to_screen.offset_x, new_y + to_screen.offset_y)

    @staticmethod
    def _map_from_top(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从源屏幕上边界映射到目标屏幕下边界

        下对齐：
        源屏幕上边界 → 目标屏幕下边界

        映射逻辑：
        - x: 按宽度比例映射
        - y: 从源屏幕上边界（比例映射）→ 目标屏幕下边界
        """
        ratio_x = x / from_screen.width
        ratio_y = y / from_screen.height

        new_x = int(ratio_x * to_screen.width)

        if to_screen.alignment == 'bottom':
            new_y = to_screen.height - 1
        elif to_screen.alignment == 'top':
            new_y = to_screen.height - int((1 - ratio_y) * to_screen.height)
        elif to_screen.alignment == 'center':
            new_y = int((to_screen.height + ratio_y * to_screen.height) / 2)
        else:
            new_y = to_screen.height - 1

        return (new_x + to_screen.offset_x, new_y + to_screen.offset_y)

    @staticmethod
    def map_to_local(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        将坐标从远程屏幕映射回本地屏幕

        Args:
            from_screen: 源屏幕（远程）
            to_screen: 目标屏幕（本地）
            x: 源屏幕上的X坐标
            y: 源屏幕上的Y坐标

        Returns:
            (目标屏幕X坐标, 目标屏幕Y坐标)
        """
        if from_screen.direction == 'left':
            return CoordinateMapper._reverse_from_left(from_screen, to_screen, x, y)
        elif from_screen.direction == 'right':
            return CoordinateMapper._reverse_from_right(from_screen, to_screen, x, y)
        elif from_screen.direction == 'top':
            return CoordinateMapper._reverse_from_top(from_screen, to_screen, x, y)
        elif from_screen.direction == 'bottom':
            return CoordinateMapper._reverse_from_bottom(from_screen, to_screen, x, y)

        return (0, 0)

    @staticmethod
    def _reverse_from_left(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从左侧远程屏幕映射回本地屏幕

        当从左侧屏幕返回时：
        - 目标屏幕右边界对应源屏幕左边界
        """
        ratio_y = y / from_screen.height

        new_x = 0
        ratio_x = x / from_screen.width
        new_x = int(ratio_x * to_screen.width)

        new_y = int(ratio_y * to_screen.height)

        return (new_x, new_y)

    @staticmethod
    def _reverse_from_right(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从右侧远程屏幕映射回本地屏幕

        当从右侧屏幕返回时：
        - 目标屏幕左边界对应源屏幕右边界
        """
        ratio_y = y / from_screen.height

        new_x = to_screen.width - 1
        ratio_x = 1 - x / from_screen.width
        new_x = int(ratio_x * to_screen.width)

        new_y = int(ratio_y * to_screen.height)

        return (new_x, new_y)

    @staticmethod
    def _reverse_from_top(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从上方远程屏幕映射回本地屏幕

        当从上方屏幕返回时：
        - 目标屏幕下边界对应源屏幕上边界
        """
        ratio_x = x / from_screen.width

        new_x = int(ratio_x * to_screen.width)
        new_y = 0

        ratio_y = y / from_screen.height
        new_y = int(ratio_y * to_screen.height)

        return (new_x, new_y)

    @staticmethod
    def _reverse_from_bottom(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从下方远程屏幕映射回本地屏幕

        当从下方屏幕返回时：
        - 目标屏幕上边界对应源屏幕下边界
        """
        ratio_x = x / from_screen.width

        new_x = int(ratio_x * to_screen.width)
        ratio_y = 1 - y / from_screen.height
        new_y = int(ratio_y * to_screen.height)

        return (new_x, new_y)

    @staticmethod
    def calculate_ratio(from_screen: ScreenLayout, to_screen: ScreenLayout) -> Tuple[float, float]:
        """
        计算两个屏幕之间的宽高比例

        Returns:
            (width_ratio, height_ratio)
        """
        width_ratio = to_screen.width / from_screen.width
        height_ratio = to_screen.height / from_screen.height
        return (width_ratio, height_ratio)
