from pynput import keyboard
from common.protocol import pack_keyboard

class KeyboardListener:
    """
    键盘事件监听器
    使用 pynput 监听本地键盘事件并打包发送
    """
    def __init__(self, on_keyboard_event=None):
        """
        初始化键盘监听器
        :param on_keyboard_event: 键盘事件回调函数，接收字节数据参数
        """
        self.listener = None
        self.on_keyboard_event = on_keyboard_event

    def start(self):
        """
        启动键盘监听
        关键步骤：
        1. 创建键盘监听器
        2. 设置回调函数
        3. 启动监听线程
        """
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        """
        停止键盘监听
        """
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_press(self, key):
        """
        处理键盘按下事件
        :param key: 按键对象
        """
        if self.on_keyboard_event:
            try:
                key_code = key.vk
            except AttributeError:
                key_code = key.value.vk
            data = pack_keyboard(key_code, True)
            self.on_keyboard_event(data)

    def _on_release(self, key):
        """
        处理键盘释放事件
        :param key: 按键对象
        """
        if self.on_keyboard_event:
            try:
                key_code = key.vk
            except AttributeError:
                key_code = key.value.vk
            data = pack_keyboard(key_code, False)
            self.on_keyboard_event(data)
