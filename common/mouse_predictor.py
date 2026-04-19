import time
import math

class MousePredictor:
    """
    鼠标移动预测器
    用于改善网络延迟导致的鼠标卡顿问题
    通过预测和插值来平滑鼠标移动
    """
    def __init__(self, history_size=5):
        """
        初始化预测器
        :param history_size: 位置历史记录数量
        """
        self.history_size = history_size
        self.position_history = []
        self.last_update_time = time.time()
        self.last_x = 0
        self.last_y = 0
        self.velocity_x = 0
        self.velocity_y = 0

    def update(self, x, y):
        """
        更新位置
        :param x: X坐标
        :param y: Y坐标
        :return: 平滑后的坐标 (x, y)
        """
        current_time = time.time()
        dt = current_time - self.last_update_time

        if dt > 0:
            self.velocity_x = (x - self.last_x) / dt
            self.velocity_y = (y - self.last_y) / dt

        self.position_history.append((x, y, current_time))
        if len(self.position_history) > self.history_size:
            self.position_history.pop(0)

        self.last_x = x
        self.last_y = y
        self.last_update_time = current_time

        return x, y

    def predict(self, lookahead_time=0.05):
        """
        预测未来位置
        :param lookahead_time: 预测的时间跨度（秒）
        :return: 预测的坐标 (x, y)
        """
        predicted_x = self.last_x + self.velocity_x * lookahead_time
        predicted_y = self.last_y + self.velocity_y * lookahead_time
        return int(predicted_x), int(predicted_y)

    def get_smoothed_position(self, target_x, target_y, smoothing_factor=0.3):
        """
        获取平滑后的位置（线性插值）
        :param target_x: 目标X坐标
        :param target_y: 目标Y坐标
        :param smoothing_factor: 平滑因子 (0-1)，越小越平滑
        :return: 平滑后的坐标 (x, y)
        """
        smoothed_x = self.last_x + (target_x - self.last_x) * smoothing_factor
        smoothed_y = self.last_y + (target_y - self.last_y) * smoothing_factor
        return int(smoothed_x), int(smoothed_y)

    def reset(self):
        """
        重置预测器状态
        """
        self.position_history.clear()
        self.last_x = 0
        self.last_y = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_update_time = time.time()


class ScreenConfig:
    """
    屏幕配置
    用于不同分辨率之间的坐标转换
    """
    def __init__(self, width=1920, height=1080):
        """
        初始化屏幕配置
        :param width: 屏幕宽度
        :param height: 屏幕高度
        """
        self.width = width
        self.height = height

    def set_resolution(self, width, height):
        """
        设置分辨率
        :param width: 屏幕宽度
        :param height: 屏幕高度
        """
        self.width = width
        self.height = height

    def scale_x(self, x, target_width):
        """
        按比例缩放X坐标
        :param x: 源X坐标
        :param target_width: 目标屏幕宽度
        :return: 缩放后的X坐标
        """
        return int(x * target_width / self.width)

    def scale_y(self, y, target_height):
        """
        按比例缩放Y坐标
        :param y: 源Y坐标
        :param target_height: 目标屏幕高度
        :return: 缩放后的Y坐标
        """
        return int(y * target_height / self.height)
