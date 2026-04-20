"""
坐标映射器

实现不同分辨率屏幕间的坐标映射计算

核心原则：
- 鼠标穿过屏幕边界时，进入方向的坐标往内偏移（避免立刻触发返回边缘检测）
- 垂直于进入方向的坐标按比例映射
- 模拟物理多屏拼接效果：光标从一边消失、从另一边同样高度位置出现

边缘偏移量 EDGE_OFFSET：切换时光标不放在像素 0 或 width-1，
而是往内偏移 EDGE_OFFSET 像素（默认 15），避免立刻触发对向边缘检测。
"""

from typing import Tuple
from .screen_layout import ScreenLayout


def _clamp(value: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(value, max_val))


EDGE_OFFSET = 15


class CoordinateMapper:
    """
    坐标映射器

    负责在不同屏幕之间进行坐标映射，考虑：
    - 屏幕对齐方式（左对齐、右对齐、上对齐、下对齐、居中对齐）
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

        仅在屏幕边界处触发映射，因此：
        - 进入坐标固定为边缘值
        - 垂直坐标按比例映射

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
    def _map_from_left(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        鼠标从本地屏幕向右移动，穿过右边缘，出现在远程屏幕的左边缘。

        物理效果：光标从本地右边缘消失，在远程屏幕左边缘同样高度位置出现。
        X 往内偏移 EDGE_OFFSET（避免立刻触发返回边缘检测），Y 按比例映射。
        """
        new_x = EDGE_OFFSET
        new_y = CoordinateMapper._map_vertical(y, from_screen.height, to_screen, 'horizontal')
        return (_clamp(new_x + to_screen.offset_x, 0, to_screen.width - 1),
                _clamp(new_y + to_screen.offset_y, 0, to_screen.height - 1))

    @staticmethod
    def _map_from_right(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        鼠标从本地屏幕向左移动，穿过左边缘，出现在远程屏幕的右边缘。

        X 往内偏移 EDGE_OFFSET（右边缘往左偏移），Y 按比例映射。
        """
        new_x = to_screen.width - 1 - EDGE_OFFSET
        new_y = CoordinateMapper._map_vertical(y, from_screen.height, to_screen, 'horizontal')
        return (_clamp(new_x + to_screen.offset_x, 0, to_screen.width - 1),
                _clamp(new_y + to_screen.offset_y, 0, to_screen.height - 1))

    @staticmethod
    def _map_from_bottom(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        鼠标从本地屏幕向上移动，穿过上边缘，出现在远程屏幕的下边缘。

        Y 往内偏移 EDGE_OFFSET（下边缘往上偏移），X 按比例映射。
        """
        new_y = to_screen.height - 1 - EDGE_OFFSET
        new_x = CoordinateMapper._map_horizontal(x, from_screen.width, to_screen, 'vertical')
        return (_clamp(new_x + to_screen.offset_x, 0, to_screen.width - 1),
                _clamp(new_y + to_screen.offset_y, 0, to_screen.height - 1))

    @staticmethod
    def _map_from_top(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        鼠标从本地屏幕向下移动，穿过下边缘，出现在远程屏幕的上边缘。

        Y 往内偏移 EDGE_OFFSET（避免立刻触发返回边缘检测），X 按比例映射。
        """
        new_y = EDGE_OFFSET
        new_x = CoordinateMapper._map_horizontal(x, from_screen.width, to_screen, 'vertical')
        return (_clamp(new_x + to_screen.offset_x, 0, to_screen.width - 1),
                _clamp(new_y + to_screen.offset_y, 0, to_screen.height - 1))

    @staticmethod
    def _map_vertical(
        y: int,
        from_height: int,
        to_screen: ScreenLayout,
        direction: str
    ) -> int:
        """
        垂直坐标映射（水平拼接时使用）

        根据对齐方式，计算目标屏幕上的 Y 坐标。

        Args:
            y: 源屏幕 Y 坐标
            from_height: 源屏幕高度
            to_screen: 目标屏幕
            direction: 'horizontal' 或 'vertical'
        """
        ratio_y = y / from_height if from_height > 0 else 0

        if to_screen.alignment in ('left', 'top'):
            new_y = int(ratio_y * to_screen.height)
        elif to_screen.alignment in ('right', 'bottom'):
            new_y = int(ratio_y * to_screen.height) + (to_screen.height - int(from_height * to_screen.height / from_height)) if from_height < to_screen.height else int(ratio_y * to_screen.height)
            height_on_to = int(from_height * to_screen.height / from_height) if from_height <= to_screen.height else to_screen.height
            offset_y = (to_screen.height - height_on_to) // 2
            if to_screen.alignment == 'right':
                offset_y = to_screen.height - height_on_to
            new_y = offset_y + int(ratio_y * height_on_to)
        elif to_screen.alignment == 'center':
            height_on_to = int(from_height * to_screen.height / from_height) if from_height > 0 else to_screen.height
            height_on_to = min(height_on_to, to_screen.height)
            offset_y = (to_screen.height - height_on_to) // 2
            new_y = offset_y + int(ratio_y * height_on_to)
        else:
            new_y = int(ratio_y * to_screen.height)

        return _clamp(new_y, 0, to_screen.height - 1)

    @staticmethod
    def _map_horizontal(
        x: int,
        from_width: int,
        to_screen: ScreenLayout,
        direction: str
    ) -> int:
        """
        水平坐标映射（垂直拼接时使用）

        根据对齐方式，计算目标屏幕上的 X 坐标。

        Args:
            x: 源屏幕 X 坐标
            from_width: 源屏幕宽度
            to_screen: 目标屏幕
            direction: 'horizontal' 或 'vertical'
        """
        ratio_x = x / from_width if from_width > 0 else 0

        if to_screen.alignment in ('left', 'top'):
            new_x = int(ratio_x * to_screen.width)
        elif to_screen.alignment in ('right', 'bottom'):
            width_on_to = int(from_width * to_screen.width / from_width) if from_width > 0 else to_screen.width
            width_on_to = min(width_on_to, to_screen.width)
            offset_x = to_screen.width - width_on_to
            new_x = offset_x + int(ratio_x * width_on_to)
        elif to_screen.alignment == 'center':
            width_on_to = int(from_width * to_screen.width / from_width) if from_width > 0 else to_screen.width
            width_on_to = min(width_on_to, to_screen.width)
            offset_x = (to_screen.width - width_on_to) // 2
            new_x = offset_x + int(ratio_x * width_on_to)
        else:
            new_x = int(ratio_x * to_screen.width)

        return _clamp(new_x, 0, to_screen.width - 1)

    @staticmethod
    def map_to_local(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        将坐标从远程屏幕映射回本地屏幕（返回操作）

        原则与 map_to_remote 相同：
        - 进入方向的坐标固定为边缘值
        - 垂直坐标按比例映射反向计算

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
        从左侧远程屏幕返回本地屏幕

        远程屏幕在本地左侧，返回时鼠标从远程右边缘 → 本地左边缘（往内偏移）
        """
        new_x = EDGE_OFFSET
        new_y = _clamp(int(y * to_screen.height / from_screen.height), 0, to_screen.height - 1)
        return (new_x, new_y)

    @staticmethod
    def _reverse_from_right(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从右侧远程屏幕返回本地屏幕

        远程屏幕在本地右侧，返回时鼠标从远程左边缘 → 本地右边缘（往内偏移）
        """
        new_x = to_screen.width - 1 - EDGE_OFFSET
        new_y = _clamp(int(y * to_screen.height / from_screen.height), 0, to_screen.height - 1)
        return (new_x, new_y)

    @staticmethod
    def _reverse_from_top(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从上方远程屏幕返回本地屏幕

        远程屏幕在本地上方，返回时鼠标从远程下边缘 → 本地上边缘（往内偏移）
        """
        new_x = _clamp(int(x * to_screen.width / from_screen.width), 0, to_screen.width - 1)
        new_y = EDGE_OFFSET
        return (new_x, new_y)

    @staticmethod
    def _reverse_from_bottom(
        from_screen: ScreenLayout,
        to_screen: ScreenLayout,
        x: int, y: int
    ) -> Tuple[int, int]:
        """
        从下方远程屏幕返回本地屏幕

        远程屏幕在本地下方，返回时鼠标从远程上边缘 → 本地下边缘（往内偏移）
        """
        new_x = _clamp(int(x * to_screen.width / from_screen.width), 0, to_screen.width - 1)
        new_y = to_screen.height - 1 - EDGE_OFFSET
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