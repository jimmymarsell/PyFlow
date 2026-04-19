from pynput import keyboard

class KeyboardController:
    """
    键盘控制器
    使用 pynput 模拟键盘事件
    """
    def __init__(self):
        """
        初始化键盘控制器
        """
        self.controller = keyboard.Controller()

    def press(self, key_code):
        """
        模拟键盘按下
        :param key_code: 按键码
        """
        try:
            key = keyboard.KeyCode.from_vk(key_code)
            self.controller.press(key)
        except Exception:
            pass

    def release(self, key_code):
        """
        模拟键盘释放
        :param key_code: 按键码
        """
        try:
            key = keyboard.KeyCode.from_vk(key_code)
            self.controller.release(key)
        except Exception:
            pass

    def type_key(self, key_code, pressed):
        """
        根据按下状态执行按键或释放
        :param key_code: 按键码
        :param pressed: 是否按下
        """
        if pressed:
            self.press(key_code)
        else:
            self.release(key_code)
