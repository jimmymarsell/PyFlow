import socket
import threading

class TCPServer:
    """
    TCP 服务端
    提供基础的 TCP 监听和客户端连接管理能力
    """
    def __init__(self, host="0.0.0.0", port=12345):
        """
        初始化 TCP 服务端
        :param host: 监听地址，默认 0.0.0.0 表示接受所有网卡连接
        :param port: 监听端口，默认 12345
        """
        self.host = host
        self.port = port
        self.server_socket = None   # 服务端 socket 对象
        self.running = False        # 服务端运行状态
        self.client_socket = None   # 已连接的客户端 socket
        self.client_thread = None   # 处理客户端的线程

    def start(self):
        """
        启动 TCP 服务端
        关键步骤：
        1、创建 socket 对象（TCP/IP）
        2、设置地址复用（避免端口占用）
        3、绑定地址和端口
        4、开始监听连接
        5、循环接受客户端连接
        """
        # 1、创建 socket：AF_INET=IPv4，SOCK_STREAM=TCP
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 2、设置 SO_REUSEADDR，允许地址复用
        # 重启程序可以立即使用同一端口，不会报 "Address already in use"
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 3、绑定地址和端口
        self.server_socket.bind((self.host, self.port))
        # 4、开始监听，参数 1 表示最多允许 1 个客户端排队
        self.server_socket.listen(1)
        self.running = True
        print(f"TCP 服务端已启动，监听地址：{self.host}:{self.port}")
        # 5、循环接受客户端连接
        while self.running:
            try:
                # 设置超时，避免 accept() 一直阻塞
                self.server_socket.settimeout(1.0)
                try:
                    # accept() 阻塞等待客户端连接
                    # 返回值：(client_socket, client_addr)
                    self.client_socket, client_addr = self.server_socket.accept()
                    print(f"TCP 客户端连接成功，地址：{client_addr}")
                    # 启动新线程处理该客户端，实现同时处理多个客户端
                    self.client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(self.client_socket, client_addr)
                    )
                    self.client_thread.daemon = True    # 主线程退出时，线程自动结束
                    self.client_thread.start()
                    # 发送欢迎消息
                    self.send_data(b"Welcome to TCP Server!\n")
                except socket.timeout:
                    # 超时后继续循环，检查 running 状态
                    continue
            except Exception as e:
                if self.running:
                    print(f"TCP 服务端接受客户端连接时出错：{e}")
                break
    
    def _handle_client(self, client_socket, client_addr):
        """
        处理客户端数据
        关键步骤：
        1、设置 socket 超时
        2、循环接收数据
        3、调用回调函数处理数据
        """
        while self.running and self.client_socket:
            try:
                # 设置超时，避免 recv() 一直阻塞
                client_socket.settimeout(0.5)
                # recv(1024) 接收最多 1024 字节数据
                # 返回 bytes 对象，空数据表示客户端断开
                data = client_socket.recv(1024)
                if not data:
                    break
                # 调用回调函数处理接收到的数据
                self.on_data_received(data)
            except socket.timeout:
                # 超时继续循环，检查连接状态
                continue
            except Exception as e:
                print(f"接收数据错误：{e}")
                break
        # 关闭客户端连接
        try:
            client_socket.close()
        except:
            pass
        print(f"客户端断开: {client_addr}")


    def send_data(self, data):
        """
        发送数据到客户端
        :param data: bytes 类型数据
        :return: 发送成功返回 True
        """
        if self.client_socket:
            try:
                # sendall() 发送所有数据，会自动重试直到完成
                self.client_socket.sendall(data)
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
        print(f"收到数据: {data}")

    def stop(self):
        """
        停止 TCP 服务端
        关键步骤：
        1. 设置 running=False 停止接受新连接
        2. 关闭客户端 socket
        3. 关闭服务端 socket
        """
        # 1、设置 running=False 停止接受新连接
        self.running = False
        # 2、关闭客户端连接
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        # 3、关闭服务端 socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("服务端已停止")

if __name__ == "__main__":
    server = TCPServer("0.0.0.0", 12345)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
