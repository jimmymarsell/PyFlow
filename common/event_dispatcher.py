from common.protocol import (
    MSG_TYPE_MOUSE_MOVE,
    MSG_TYPE_MOUSE_BUTTON,
    MSG_TYPE_MOUSE_SCROLL,
    MSG_TYPE_KEYBOARD,
    MSG_TYPE_CLIPBOARD,
    MSG_TYPE_HEARTBEAT,
    MSG_TYPE_SWITCH,
    unpack_mouse_move,
    unpack_mouse_button,
    unpack_mouse_scroll,
    unpack_keyboard,
    unpack_clipboard,
    unpack_switch,
    get_msg_type,
    get_msg_size
)

class EventDispatcher:
    """
    事件分发器
    根据消息类型将事件分发给对应的处理器
    """
    def __init__(self):
        """
        初始化事件分发器
        """
        self._handlers = {}
        self._buffer = b""

    def register(self, msg_type, handler):
        """
        注册消息类型对应的处理器
        :param msg_type: 消息类型
        :param handler: 处理函数
        """
        self._handlers[msg_type] = handler

    def dispatch(self, data):
        """
        分发事件到对应的处理器
        关键步骤：
        1. 将数据添加到缓冲区
        2. 循环解析完整消息
        3. 调用处理器执行
        """
        self._buffer += data
        while len(self._buffer) > 0:
            msg_type = get_msg_type(self._buffer)
            if msg_type is None:
                break
            expected_size = get_msg_size(msg_type)
            if expected_size == 0:
                self._buffer = b""
                break
            if len(self._buffer) < expected_size:
                break
            msg_data = self._buffer[:expected_size]
            self._buffer = self._buffer[expected_size:]
            handler = self._handlers.get(msg_type)
            if handler is None:
                continue
            try:
                if msg_type == MSG_TYPE_MOUSE_MOVE:
                    x, y = unpack_mouse_move(msg_data)
                    handler(x=x, y=y)
                elif msg_type == MSG_TYPE_MOUSE_BUTTON:
                    button, pressed, x, y = unpack_mouse_button(msg_data)
                    handler(button=button, pressed=pressed, x=x, y=y)
                elif msg_type == MSG_TYPE_MOUSE_SCROLL:
                    x, y, dx, dy = unpack_mouse_scroll(msg_data)
                    handler(x=x, y=y, dx=dx, dy=dy)
                elif msg_type == MSG_TYPE_KEYBOARD:
                    key_code, pressed = unpack_keyboard(msg_data)
                    handler(key_code=key_code, pressed=pressed)
                elif msg_type == MSG_TYPE_CLIPBOARD:
                    content = unpack_clipboard(msg_data)
                    handler(content=content)
                elif msg_type == MSG_TYPE_HEARTBEAT:
                    handler()
                elif msg_type == MSG_TYPE_SWITCH:
                    target_x, target_y, action = unpack_switch(msg_data)
                    handler(target_x=target_x, target_y=target_y, action=action)
            except Exception as e:
                print(f"Event dispatch error: {e}")

if __name__ == "__main__":
    def test_move_handler(x, y):
        print(f"Move handler: x={x}, y={y}")

    def test_button_handler(button, pressed, x, y):
        print(f"Button handler: button={button}, pressed={pressed}, x={x}, y={y}")

    dispatcher = EventDispatcher()
    dispatcher.register(MSG_TYPE_MOUSE_MOVE, test_move_handler)
    dispatcher.register(MSG_TYPE_MOUSE_BUTTON, test_button_handler)

    from common.protocol import pack_mouse_move, pack_mouse_button
    move_data = pack_mouse_move(100, 200)
    dispatcher.dispatch(move_data)

    button_data = pack_mouse_button(1, True, 300, 400)
    dispatcher.dispatch(button_data)