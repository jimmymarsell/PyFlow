import struct

MSG_TYPE_MOUSE_MOVE = 0x01
MSG_TYPE_MOUSE_BUTTON = 0x02
MSG_TYPE_MOUSE_SCROLL = 0x03
MSG_TYPE_KEYBOARD = 0x04
MSG_TYPE_CLIPBOARD = 0x05
MSG_TYPE_SWITCH = 0x06
MSG_TYPE_SWITCH_ACK = 0x07
MSG_TYPE_HEARTBEAT = 0xFF

MOUSE_EVENT_SIZE = 9
KEYBOARD_EVENT_SIZE = 6
HEARTBEAT_SIZE = 1
SWITCH_EVENT_SIZE = 13

STRUCT_FORMAT = ">Bii"
STRUCT_FORMAT_KEYB = ">BiBB2s"
STRUCT_FORMAT_HEARTBEAT = ">B"

def pack_mouse_move(x, y):
    """
    打包鼠标移动事件
    :param x: X坐标
    :param y: Y坐标
    :return: 打包后的字节数据
    """
    data = struct.pack(STRUCT_FORMAT, MSG_TYPE_MOUSE_MOVE, x, y)
    return data

def unpack_mouse_move(data):
    """
    解包鼠标移动事件
    :param data: 字节数据
    :return: (x, y) 元组
    """
    msg_type, x, y = struct.unpack(STRUCT_FORMAT, data)
    return x, y

def pack_mouse_button(button, pressed, x, y):
    """
    打包鼠标按钮事件
    :param button: 按钮编号 (1=左键, 2=右键)
    :param pressed: 是否按下
    :param x: X坐标
    :param y: Y坐标
    :return: 打包后的字节数据
    """
    data = struct.pack(">Biiii", MSG_TYPE_MOUSE_BUTTON, button, 1 if pressed else 0, x, y)
    return data

def unpack_mouse_button(data):
    """
    解包鼠标按钮事件
    :param data: 字节数据
    :return: (button, pressed, x, y) 元组
    """
    msg_type, button, pressed, x, y = struct.unpack(">Biiii", data)
    return button, bool(pressed), x, y

def pack_mouse_scroll(x, y, dx, dy):
    """
    打包鼠标滚动事件
    :param x: X坐标
    :param y: Y坐标
    :param dx: 水平滚动量
    :param dy: 垂直滚动量
    :return: 打包后的字节数据
    """
    data = struct.pack(">Biiii", MSG_TYPE_MOUSE_SCROLL, x, y, dx, dy)
    return data

def unpack_mouse_scroll(data):
    """
    解包鼠标滚动事件
    :param data: 字节数据
    :return: (x, y, dx, dy) 元组
    """
    msg_type, x, y, dx, dy = struct.unpack(">Biiii", data)
    return x, y, dx, dy

def pack_keyboard(key_code, pressed):
    """
    打包键盘事件
    :param key_code: 按键码
    :param pressed: 是否按下
    :return: 打包后的字节数据
    """
    data = struct.pack(STRUCT_FORMAT_KEYB, MSG_TYPE_KEYBOARD, key_code, 1 if pressed else 0, 0, b'\x00\x00')
    return data

def unpack_keyboard(data):
    """
    解包键盘事件
    :param data: 字节数据
    :return: (key_code, pressed) 元组
    """
    msg_type, key_code, pressed, _, _ = struct.unpack(STRUCT_FORMAT_KEYB, data)
    return key_code, bool(pressed)

def pack_clipboard(content):
    """
    打包剪贴板内容
    :param content: 剪贴板内容 (str 或 bytes)
    :return: 打包后的字节数据
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    length = len(content)
    data = struct.pack(">BH", MSG_TYPE_CLIPBOARD, length) + content
    return data

def unpack_clipboard(data):
    """
    解包剪贴板内容
    :param data: 字节数据
    :return: 剪贴板内容字符串
    """
    msg_type, length = struct.unpack(">BH", data[:3])
    content = data[3:3+length]
    return content.decode('utf-8')

def pack_switch(target_x, target_y, action):
    """
    打包屏幕切换命令
    :param target_x: 目标X坐标
    :param target_y: 目标Y坐标
    :param action: 切换动作 (0=切换到远程, 1=返回本地)
    :return: 打包后的字节数据
    """
    data = struct.pack(">Biii", MSG_TYPE_SWITCH, target_x, target_y, action)
    return data

def unpack_switch(data):
    """
    解包屏幕切换命令
    :param data: 字节数据
    :return: (target_x, target_y, action) 元组
    """
    msg_type, target_x, target_y, action = struct.unpack(">Biii", data)
    return target_x, target_y, action

def pack_heartbeat():
    """
    打包心跳包
    :return: 打包后的字节数据
    """
    return struct.pack(STRUCT_FORMAT_HEARTBEAT, MSG_TYPE_HEARTBEAT)

def get_msg_type(data):
    """
    获取消息类型
    :param data: 字节数据
    :return: 消息类型 (int) 或 None
    """
    if not data:
        return None
    return data[0]

def get_msg_size(msg_type):
    """
    根据消息类型获取期望的消息长度
    :param msg_type: 消息类型
    :return: 期望的字节长度
    """
    if msg_type == MSG_TYPE_MOUSE_MOVE:
        return 9
    elif msg_type in (MSG_TYPE_MOUSE_BUTTON, MSG_TYPE_MOUSE_SCROLL):
        return 17
    elif msg_type == MSG_TYPE_KEYBOARD:
        return 9
    elif msg_type == MSG_TYPE_SWITCH:
        return 13
    elif msg_type == MSG_TYPE_HEARTBEAT:
        return 1
    elif msg_type == MSG_TYPE_CLIPBOARD:
        return 3
    return 0

class Message:
    """
    消息封装类
    用于将消息类型和负载封装为对象
    """
    def __init__(self, msg_type, payload=None):
        """
        初始化消息
        :param msg_type: 消息类型
        :param payload: 负载数据 (dict)
        """
        self.msg_type = msg_type
        self.payload = payload

    def to_bytes(self):
        """
        将消息转换为字节数据
        :return: 打包后的字节数据
        """
        if self.msg_type == MSG_TYPE_MOUSE_MOVE:
            return pack_mouse_move(self.payload['x'], self.payload['y'])
        elif self.msg_type == MSG_TYPE_MOUSE_BUTTON:
            return pack_mouse_button(
                self.payload['button'],
                self.payload['pressed'],
                self.payload.get('x', 0),
                self.payload.get('y', 0)
            )
        elif self.msg_type == MSG_TYPE_MOUSE_SCROLL:
            return pack_mouse_scroll(
                self.payload.get('x', 0),
                self.payload.get('y', 0),
                self.payload.get('dx', 0),
                self.payload.get('dy', 0)
            )
        elif self.msg_type == MSG_TYPE_KEYBOARD:
            return pack_keyboard(self.payload['key_code'], self.payload['pressed'])
        elif self.msg_type == MSG_TYPE_CLIPBOARD:
            return pack_clipboard(self.payload['content'])
        elif self.msg_type == MSG_TYPE_SWITCH:
            return pack_switch(
                self.payload.get('target_x', 0),
                self.payload.get('target_y', 0),
                self.payload.get('action', 0)
            )
        elif self.msg_type == MSG_TYPE_HEARTBEAT:
            return pack_heartbeat()
        return b''

    @staticmethod
    def from_bytes(data):
        """
        从字节数据创建消息对象
        :param data: 字节数据
        :return: Message 对象或 None
        """
        if not data:
            return None
        msg_type = data[0]
        if msg_type == MSG_TYPE_MOUSE_MOVE:
            x, y = unpack_mouse_move(data)
            return Message(msg_type, {'x': x, 'y': y})
        elif msg_type == MSG_TYPE_MOUSE_BUTTON:
            button, pressed, x, y = unpack_mouse_button(data)
            return Message(msg_type, {'button': button, 'pressed': pressed, 'x': x, 'y': y})
        elif msg_type == MSG_TYPE_MOUSE_SCROLL:
            x, y, dx, dy = unpack_mouse_scroll(data)
            return Message(msg_type, {'x': x, 'y': y, 'dx': dx, 'dy': dy})
        elif msg_type == MSG_TYPE_KEYBOARD:
            key_code, pressed = unpack_keyboard(data)
            return Message(msg_type, {'key_code': key_code, 'pressed': pressed})
        elif msg_type == MSG_TYPE_CLIPBOARD:
            content = unpack_clipboard(data)
            return Message(msg_type, {'content': content})
        elif msg_type == MSG_TYPE_SWITCH:
            target_x, target_y, action = unpack_switch(data)
            return Message(msg_type, {'target_x': target_x, 'target_y': target_y, 'action': action})
        elif msg_type == MSG_TYPE_HEARTBEAT:
            return Message(msg_type)
        return None

if __name__ == "__main__":
    """
    协议测试代码
    """
    move_data = pack_mouse_move(100, 200)
    print(f"Mouse move packed: {len(move_data)} bytes, hex: {move_data.hex()}")

    x, y = unpack_mouse_move(move_data)
    print(f"Mouse move unpacked: x={x}, y={y}")

    key_data = pack_keyboard(65, True)
    print(f"Key packed: {len(key_data)} bytes, hex: {key_data.hex()}")

    key_code, pressed = unpack_keyboard(key_data)
    print(f"Key unpacked: key_code={key_code}, pressed={pressed}")

    clip_data = pack_clipboard("Hello PyFlow")
    print(f"Clipboard packed: {len(clip_data)} bytes")

    content = unpack_clipboard(clip_data)
    print(f"Clipboard unpacked: {content}")

    hb = pack_heartbeat()
    print(f"Heartbeat packed: {hb.hex()}")