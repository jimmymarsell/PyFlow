from pynput import mouse
from common.protocol import pack_mouse_move, pack_mouse_button, pack_mouse_scroll

BUTTON_MAP = {
    'left': 1,
    'right': 2,
    'middle': 3,
    'x1': 4,
    'x2': 5,
}

class MouseListener:
    """
    鼠标事件监听器
    使用 pynput 监听本地鼠标事件并打包发送
    """
    def __init__(self, on_mouse_event=None):
        """
        初始化鼠标监听器
        :param on_mouse_event: 鼠标事件回调函数，接收字节数据参数
        """
        self.listener = None
        self.on_mouse_event = on_mouse_event
        self._last_x = 0
        self._last_y = 0

    def start(self):
        """
        启动鼠标监听
        关键步骤：
        1. 创建鼠标监听器
        2. 设置回调函数
        3. 启动监听线程
        """
        self.listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.listener.start()

    def stop(self):
        """
        停止鼠标监听
        """
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_move(self, x, y):
        """
        处理鼠标移动事件
        :param x: X坐标
        :param y: Y坐标
        """
        self._last_x = x
        self._last_y = y
        if self.on_mouse_event:
            data = pack_mouse_move(x, y)
            self.on_mouse_event(data)

    def _on_click(self, x, y, button, pressed):
        """
        处理鼠标点击事件
        :param x: X坐标
        :param y: Y坐标
        :param button: 按钮
        :param pressed: 是否按下
        """
        self._last_x = x
        self._last_y = y
        if self.on_mouse_event:
            data = pack_mouse_button(BUTTON_MAP.get(button.name, 0), pressed, x, y)
            self.on_mouse_event(data)

    def _on_scroll(self, x, y, dx, dy):
        """
        处理鼠标滚动事件
        :param x: X坐标
        :param y: Y坐标
        :param dx: 水平滚动量
        :param dy: 垂直滚动量
        """
        self._last_x = x
        self._last_y = y
        if self.on_mouse_event:
            data = pack_mouse_scroll(x, y, dx, dy)
            self.on_mouse_event(data)

if __name__ == "__main__":
    """
    鼠标监听器测试代码
    """
    def test_handler(data):
        print(f"Mouse event: {data.hex()}")

    listener = MouseListener(on_mouse_event=test_handler)
    listener.start()
    print("Mouse listener started. Press Ctrl+C to exit.")
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        print("Mouse listener stopped.")