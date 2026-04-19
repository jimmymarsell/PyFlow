import socket
import threading

class TCPClient:
    """
    TCP 客户端
    提供基础的 TCP 连接和数据收发能力
    """
    def __init__(self):
        """
        初始化 TCP 客户端
        """
        self.socket = None           # 客户端 socket 对象
        self.connected = False       # 连接状态
        self.recv_thread = None      # 接收线程

    def connect(self, host, port):
        """
        连接到 TCP 服务端
        关键步骤：
        1. 创建 socket 对象
        2. 连接到服务端
        3. 启动接收线程
        """
        try:
            # 1. 创建 socket：IPv4 + TCP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 2. 连接到服务端（阻塞操作）
            # connect() 会尝试与服务端建立 TCP 连接
            self.socket.connect((host, port))
            self.connected = True
            print(f"已连接到服务端 {host}:{port}")
            
            # 3. 启动接收线程
            self.recv_thread = threading.Thread(target=self._recv_loop)
            self.recv_thread.daemon = True
            self.recv_thread.start()
            
            return True
        except Exception as e:
            print(f"连接服务端失败: {e}")
            self.connected = False
            return False

    def _recv_loop(self):
        """
        接收数据循环
        关键步骤：
        1. 设置 socket 超时
        2. 循环接收数据
        3. 调用回调处理数据
        """
        while self.connected:
            try:
                # 设置超时，避免 recv() 一直阻塞
                self.socket.settimeout(0.5)
                
                # recv() 接收数据，返回 bytes 对象
                # 空数据表示服务端断开连接
                data = self.socket.recv(1024)
                if not data:
                    print("服务端已断开连接")
                    break
                
                # 调用回调函数处理接收到的数据
                self.on_data_received(data)
                
            except socket.timeout:
                # 超时继续循环，检查连接状态
                continue
            except Exception as e:
                if self.connected:
                    print(f"接收数据错误: {e}")
                break
        
        self.connected = False
        print("接收线程已结束")

    def send_data(self, data):
        """
        发送数据到服务端
        :param data: bytes 类型数据
        :return: 发送成功返回 True
        """
        if self.socket and self.connected:
            try:
                # sendall() 发送所有数据
                self.socket.sendall(data)
                return True
            except Exception as e:
                print(f"发送数据错误: {e}")
                return False
        return False

    def on_data_received(self, data):
        """
        数据接收回调（子类可重写）
        :param data: 接收到的 bytes 数据
        """
        print(f"收到服务端数据: {data}")

    def disconnect(self):
        """
        断开 TCP 连接
        关键步骤：
        1. 设置 connected=False 停止接收线程
        2. 关闭 socket
        """
        # 1. 设置连接状态为 False
        self.connected = False
        
        # 2. 关闭 socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("已断开与服务端的连接")

if __name__ == "__main__":
    client = TCPClient()
    try:
        if client.connect("127.0.0.1", 12345):
            # 发送测试数据
            client.send_data(b"Hello Server!")
            # 保持运行
            import time
            while client.connected:
                time.sleep(1)
    except KeyboardInterrupt:
        client.disconnect()