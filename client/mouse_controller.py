from pynput import mouse
from pynput.mouse import Button

class MouseController:
    """
    鼠标控制器
    使用 pynput 模拟鼠标事件
    """
    def __init__(self):
        """
        初始化鼠标控制器
        """
        self.controller = mouse.Controller()
        self._last_position = (0, 0)

    def move_to(self, x, y):
        """
        移动鼠标到绝对位置
        :param x: X坐标
        :param y: Y坐标
        """
        self.controller.position = (int(x), int(y))
        self._last_position = (int(x), int(y))

    def move_relative(self, dx, dy):
        """
        相对移动鼠标
        :param dx: X方向增量
        :param dy: Y方向增量
        """
        current = self.controller.position
        new_x = current[0] + int(dx)
        new_y = current[1] + int(dy)
        self.controller.position = (new_x, new_y)
        self._last_position = (new_x, new_y)

    def click(self, button, pressed, x, y):
        """
        模拟鼠标点击
        :param button: 按钮编号 (1=左键, 2=右键)
        :param pressed: 是否按下
        :param x: X坐标
        :param y: Y坐标
        """
        if pressed:
            self.controller.position = (int(x), int(y))
            self.controller.press(Button.left if button == 1 else Button.right)
        else:
            self.controller.position = (int(x), int(y))
            self.controller.release(Button.left if button == 1 else Button.right)

    def scroll(self, x, y, dx, dy):
        """
        模拟鼠标滚动
        :param x: X坐标
        :param y: Y坐标
        :param dx: 水平滚动量
        :param dy: 垂直滚动量
        """
        self.controller.scroll(int(dx), int(dy))

    def get_position(self):
        """
        获取当前鼠标位置
        :return: (x, y) 元组
        """
        return self.controller.position

if __name__ == "__main__":
    """
    鼠标控制器测试代码
    """
    ctrl = MouseController()
    print("Current position:", ctrl.get_position())
    ctrl.move_to(500, 500)
    print("After move_to(500, 500):", ctrl.get_position())
    ctrl.move_relative(100, 100)
    print("After move_relative(100, 100):", ctrl.get_position())