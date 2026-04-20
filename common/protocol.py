import struct

MSG_TYPE_MOUSE_MOVE = 0x01
MSG_TYPE_MOUSE_BUTTON = 0x02
MSG_TYPE_MOUSE_SCROLL = 0x03
MSG_TYPE_KEYBOARD = 0x04
MSG_TYPE_CLIPBOARD = 0x05
MSG_TYPE_SWITCH = 0x06
MSG_TYPE_SWITCH_ACK = 0x07
MSG_TYPE_MOUSE_DELTA = 0x08
MSG_TYPE_HEARTBEAT = 0xFF

MOUSE_EVENT_SIZE = 9
KEYBOARD_EVENT_SIZE = 6
HEARTBEAT_SIZE = 1
SWITCH_EVENT_SIZE = 17

STRUCT_FORMAT = ">Bii"
STRUCT_FORMAT_KEYB = ">BiBB2s"
STRUCT_FORMAT_HEARTBEAT = ">B"
STRUCT_FORMAT_DELTA = ">Bhh"


def pack_mouse_move(x, y):
    data = struct.pack(STRUCT_FORMAT, MSG_TYPE_MOUSE_MOVE, x, y)
    return data


def unpack_mouse_move(data):
    msg_type, x, y = struct.unpack(STRUCT_FORMAT, data)
    return x, y


def pack_mouse_delta(dx, dy):
    data = struct.pack(STRUCT_FORMAT_DELTA, MSG_TYPE_MOUSE_DELTA, dx, dy)
    return data


def unpack_mouse_delta(data):
    _, dx, dy = struct.unpack(STRUCT_FORMAT_DELTA, data)
    return dx, dy


def pack_mouse_button(button, pressed, x, y):
    data = struct.pack(">Biiii", MSG_TYPE_MOUSE_BUTTON, button, 1 if pressed else 0, x, y)
    return data


def unpack_mouse_button(data):
    msg_type, button, pressed, x, y = struct.unpack(">Biiii", data)
    return button, bool(pressed), x, y


def pack_mouse_scroll(x, y, dx, dy):
    data = struct.pack(">Biiii", MSG_TYPE_MOUSE_SCROLL, x, y, dx, dy)
    return data


def unpack_mouse_scroll(data):
    msg_type, x, y, dx, dy = struct.unpack(">Biiii", data)
    return x, y, dx, dy


def pack_keyboard(key_code, pressed):
    data = struct.pack(STRUCT_FORMAT_KEYB, MSG_TYPE_KEYBOARD, key_code, 1 if pressed else 0, 0, b'\x00\x00')
    return data


def unpack_keyboard(data):
    msg_type, key_code, pressed, _, _ = struct.unpack(STRUCT_FORMAT_KEYB, data)
    return key_code, bool(pressed)


def pack_clipboard(content):
    if isinstance(content, str):
        content = content.encode('utf-8')
    length = len(content)
    data = struct.pack(">BH", MSG_TYPE_CLIPBOARD, length) + content
    return data


def unpack_clipboard(data):
    msg_type, length = struct.unpack(">BH", data[:3])
    content = data[3:3 + length]
    return content.decode('utf-8')


def pack_switch(target_x, target_y, action, screen_w=0, screen_h=0):
    data = struct.pack(">BiiiHH", MSG_TYPE_SWITCH, target_x, target_y, action, screen_w, screen_h)
    return data


def unpack_switch(data):
    _, target_x, target_y, action, screen_w, screen_h = struct.unpack(">BiiiHH", data)
    return target_x, target_y, action, screen_w, screen_h


def pack_switch_ack(switch_id):
    return struct.pack(">BI", MSG_TYPE_SWITCH_ACK, switch_id)


def unpack_switch_ack(data):
    _, switch_id = struct.unpack(">BI", data)
    return switch_id


def pack_heartbeat():
    return struct.pack(STRUCT_FORMAT_HEARTBEAT, MSG_TYPE_HEARTBEAT)


def get_msg_type(data):
    if not data:
        return None
    return data[0]


def get_msg_size(msg_type):
    if msg_type == MSG_TYPE_MOUSE_MOVE:
        return 9
    elif msg_type in (MSG_TYPE_MOUSE_BUTTON, MSG_TYPE_MOUSE_SCROLL):
        return 17
    elif msg_type == MSG_TYPE_KEYBOARD:
        return 9
    elif msg_type == MSG_TYPE_SWITCH:
        return 17
    elif msg_type == MSG_TYPE_SWITCH_ACK:
        return 5
    elif msg_type == MSG_TYPE_MOUSE_DELTA:
        return 5
    elif msg_type == MSG_TYPE_HEARTBEAT:
        return 1
    elif msg_type == MSG_TYPE_CLIPBOARD:
        return 0
    return 0


class Message:
    def __init__(self, msg_type, payload=None):
        self.msg_type = msg_type
        self.payload = payload

    def to_bytes(self):
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
                self.payload.get('action', 0),
                self.payload.get('screen_w', 0),
                self.payload.get('screen_h', 0)
            )
        elif self.msg_type == MSG_TYPE_MOUSE_DELTA:
            return pack_mouse_delta(self.payload.get('dx', 0), self.payload.get('dy', 0))
        elif self.msg_type == MSG_TYPE_SWITCH_ACK:
            return pack_switch_ack(self.payload.get('switch_id', 0))
        elif self.msg_type == MSG_TYPE_HEARTBEAT:
            return pack_heartbeat()
        return b''

    @staticmethod
    def from_bytes(data):
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
            target_x, target_y, action, screen_w, screen_h = unpack_switch(data)
            return Message(msg_type, {'target_x': target_x, 'target_y': target_y, 'action': action, 'screen_w': screen_w, 'screen_h': screen_h})
        elif msg_type == MSG_TYPE_SWITCH_ACK:
            switch_id = unpack_switch_ack(data)
            return Message(msg_type, {'switch_id': switch_id})
        elif msg_type == MSG_TYPE_MOUSE_DELTA:
            dx, dy = unpack_mouse_delta(data)
            return Message(msg_type, {'dx': dx, 'dy': dy})
        elif msg_type == MSG_TYPE_HEARTBEAT:
            return Message(msg_type)
        return None


if __name__ == "__main__":
    move_data = pack_mouse_move(100, 200)
    print(f"Mouse move packed: {len(move_data)} bytes, hex: {move_data.hex()}")
    x, y = unpack_mouse_move(move_data)
    print(f"Mouse move unpacked: x={x}, y={y}")

    delta_data = pack_mouse_delta(3, -5)
    print(f"Mouse delta packed: {len(delta_data)} bytes, hex: {delta_data.hex()}")
    dx, dy = unpack_mouse_delta(delta_data)
    print(f"Mouse delta unpacked: dx={dx}, dy={dy}")

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

    ack_data = pack_switch_ack(42)
    print(f"Switch ACK packed: {len(ack_data)} bytes, hex: {ack_data.hex()}")
    sid = unpack_switch_ack(ack_data)
    print(f"Switch ACK unpacked: switch_id={sid}")