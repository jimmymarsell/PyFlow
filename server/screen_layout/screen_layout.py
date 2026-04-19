"""
屏幕布局数据类

定义屏幕布局配置的数据结构
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScreenLayout:
    """
    屏幕布局配置数据类

    属性说明：
    - screen_id: 屏幕唯一标识符
    - host: 被控端 IP 地址（本地屏幕为 None）
    - port: 被控端端口（本地屏幕为 0）
    - width: 屏幕宽度（像素）
    - height: 屏幕高度（像素）
    - direction: 拼接方向，相对于主控端的位置
    - alignment: 对齐方式，影响坐标映射计算
    - offset_x: X方向微调偏移（用于精确对齐）
    - offset_y: Y方向微调偏移
    - edge_margin: 边缘触发阈值（像素）
    - is_local: 是否为本地屏幕
    - name: 屏幕名称（可选）
    """
    screen_id: str
    host: Optional[str] = None
    port: int = 0
    width: int = 0
    height: int = 0
    direction: str = 'right'
    alignment: str = 'left'
    offset_x: int = 0
    offset_y: int = 0
    edge_margin: int = 10
    is_local: bool = False
    name: str = ''

    def __post_init__(self):
        """验证配置参数"""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width 和 height 必须大于 0")

        if not self.is_local:
            valid_directions = {'left', 'right', 'top', 'bottom'}
            if self.direction not in valid_directions:
                raise ValueError(f"direction 必须是 {valid_directions} 之一")

            valid_alignments = {'left', 'right', 'top', 'bottom', 'center'}
            if self.alignment not in valid_alignments:
                raise ValueError(f"alignment 必须是 {valid_alignments} 之一")

            if self.edge_margin < 0:
                raise ValueError("edge_margin 必须大于等于 0")

            if not self.host:
                raise ValueError("远程屏幕必须指定 host")
            if self.port <= 0:
                raise ValueError("远程屏幕必须指定 port")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.screen_id,
            'host': self.host,
            'port': self.port,
            'width': self.width,
            'height': self.height,
            'direction': self.direction,
            'alignment': self.alignment,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'edge_margin': self.edge_margin,
            'is_local': self.is_local,
            'name': self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ScreenLayout':
        """从字典创建"""
        return cls(
            screen_id=data.get('id', data.get('screen_id', '')),
            host=data.get('host'),
            port=data.get('port', 0),
            width=data.get('width', 0),
            height=data.get('height', 0),
            direction=data.get('direction', 'right'),
            alignment=data.get('alignment', 'left'),
            offset_x=data.get('offset_x', 0),
            offset_y=data.get('offset_y', 0),
            edge_margin=data.get('edge_margin', 10),
            is_local=data.get('is_local', False),
            name=data.get('name', ''),
        )

    def get_bounds(self) -> dict:
        """
        获取屏幕边界坐标

        返回虚拟坐标系中的边界：
        - 对于本地屏幕，原点为 (0, 0)
        - 对于远程屏幕，根据 direction 计算偏移
        """
        offset = self.get_offset()
        return {
            'left': offset['x'],
            'top': offset['y'],
            'right': offset['x'] + self.width,
            'bottom': offset['y'] + self.height,
        }

    def get_offset(self) -> dict:
        """获取屏幕在虚拟坐标系中的偏移量"""
        return {'x': self.offset_x, 'y': self.offset_y}

    def contains_point(self, x: int, y: int) -> bool:
        """检查点是否在此屏幕内"""
        bounds = self.get_bounds()
        return (bounds['left'] <= x < bounds['right'] and
                bounds['top'] <= y < bounds['bottom'])
