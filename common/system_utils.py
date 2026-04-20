import platform
import socket
import ctypes


def get_system_platform():
    return platform.system()


def get_screen_size():
    import pyautogui
    return pyautogui.size()


def get_local_ip():
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except socket.error:
        ip = None
    return ip


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def hide_cursor():
    system = platform.system()
    if system == 'Windows':
        ctypes.windll.user32.ShowCursor(False)


def show_cursor():
    system = platform.system()
    if system == 'Windows':
        ctypes.windll.user32.ShowCursor(True)


if __name__ == "__main__":
    local_platform = get_system_platform()
    print("当前操作系统:", local_platform)
    print("是否管理员权限:", "是" if is_admin() else "否")