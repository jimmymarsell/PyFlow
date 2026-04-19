import platform
import socket
import pyautogui
import ctypes

def get_system_platform():
    """
    获取当前操作系统
    :return: "Windows"、"macOS" 或 "Linux"
    """
    return platform.system()

def get_screen_size():
    """
    获取屏幕分辨率
    :return: (width, height) 元组
    """
    return pyautogui.size()

def get_local_ip():
    """
    获取本机局域网 IP 地址
    :return: IP 地址字符串，如果获取失败则返回 None
    """
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except socket.error:
        ip = None
    return ip

def is_admin():
    """
    检查是否以管理员权限运行（Windows）
    :return: True 表示有管理员权限，False 表示没有
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    local_platform = get_system_platform()
    print("当前操作系统:", local_platform)
    size = get_screen_size()
    print("屏幕分辨率:", size)
    print("屏幕宽度:", size[0])
    print("屏幕高度:", size[1])
    ip = get_local_ip()
    print("本机IP地址:", ip)
    admin = is_admin()
    print("是否管理员权限:", "是" if admin else "否")