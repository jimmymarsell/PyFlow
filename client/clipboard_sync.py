import pyperclip

class ClipboardSync:
    """
    剪贴板同步器
    接收远程剪贴板内容并更新本地剪贴板
    """
    def __init__(self):
        """
        初始化剪贴板同步器
        """
        self._last_content = ""

    def update_clipboard(self, content):
        """
        更新本地剪贴板
        :param content: 剪贴板内容
        """
        if content == self._last_content:
            return
        try:
            pyperclip.copy(content)
            self._last_content = content
        except Exception:
            pass

    def get_current_content(self):
        """
        获取当前剪贴板内容
        :return: 剪贴板文本内容
        """
        try:
            return pyperclip.paste()
        except Exception:
            return ""
