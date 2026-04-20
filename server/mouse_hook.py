"""
Windows 低级鼠标钩子模块

远程控制模式下拦截所有鼠标事件，阻止传递给OS。
"""

import ctypes
import ctypes.wintypes
import threading

LRESULT = ctypes.c_long

WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEWHEEL = 0x020A


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_ulong),
    ]


LPMSLLHOOKSTRUCT = ctypes.POINTER(MSLLHOOKSTRUCT)

HOOKPROC = ctypes.CFUNCTYPE(LRESULT, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class MouseHook:
    """Windows 低级鼠标钩子管理器"""

    def __init__(self, on_move=None, on_button=None, on_scroll=None):
        self._on_move = on_move
        self._on_button = on_button
        self._on_scroll = on_scroll
        self._hook = None
        self._hook_proc = None
        self._thread = None
        self._running = False
        self._active = False
        self._last_x = 0
        self._last_y = 0
        self._has_last = False

    def install(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._hook_loop, daemon=True)
        self._thread.start()

    def uninstall(self):
        self._running = False
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def set_active(self, active):
        self._active = active
        if active:
            self._has_last = False

    def set_last_position(self, x, y):
        self._last_x = x
        self._last_y = y
        self._has_last = True

    def _hook_loop(self):
        self._hook_proc = HOOKPROC(self._ll_mouse_proc)
        self._hook = user32.SetWindowsHookExA(
            WH_MOUSE_LL,
            self._hook_proc,
            kernel32.GetModuleHandleA(b'__main__'),
            0
        )
        if not self._hook:
            err = ctypes.GetLastError()
            print(f"[MouseHook] SetWindowsHookEx 失败, error={err}")
            self._running = False
            return

        print("[MouseHook] 钩子已安装，消息循环启动")
        msg = ctypes.wintypes.MSG()
        while self._running:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result == 0 or result == -1:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
        print("[MouseHook] 钩子已卸载")

    def _ll_mouse_proc(self, nCode, wParam, lParam):
        if nCode >= 0 and self._active:
            try:
                info = ctypes.cast(lParam, LPMSLLHOOKSTRUCT).contents
                x = info.x
                y = info.y
                mouse_data = info.mouseData
            except Exception:
                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

            if wParam == WM_MOUSEMOVE:
                if self._has_last:
                    dx = x - self._last_x
                    dy = y - self._last_y
                    if abs(dx) >= 1 or abs(dy) >= 1:
                        if self._on_move:
                            try:
                                self._on_move(dx, dy)
                            except Exception:
                                pass

                screen_w = user32.GetSystemMetrics(0)
                screen_h = user32.GetSystemMetrics(1)
                cx = screen_w // 2
                cy = screen_h // 2
                user32.SetCursorPos(cx, cy)
                self._last_x = cx
                self._last_y = cy
                self._has_last = True
                return 1  # block event

            elif wParam in (WM_LBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONDOWN,
                           WM_RBUTTONUP, WM_MBUTTONDOWN, WM_MBUTTONUP):
                button = 0
                pressed = False
                if wParam == WM_LBUTTONDOWN:
                    button, pressed = 1, True
                elif wParam == WM_LBUTTONUP:
                    button, pressed = 1, False
                elif wParam == WM_RBUTTONDOWN:
                    button, pressed = 2, True
                elif wParam == WM_RBUTTONUP:
                    button, pressed = 2, False
                elif wParam == WM_MBUTTONDOWN:
                    button, pressed = 3, True
                elif wParam == WM_MBUTTONUP:
                    button, pressed = 3, False
                if self._on_button and button > 0:
                    try:
                        self._on_button(button, pressed)
                    except Exception:
                        pass
                return 1

            elif wParam == WM_MOUSEWHEEL:
                delta = ctypes.c_short(mouse_data >> 16).value
                if self._on_scroll:
                    try:
                        self._on_scroll(0, delta)
                    except Exception:
                        pass
                return 1

        return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)