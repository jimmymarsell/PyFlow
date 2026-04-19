import sys
import signal
from config import parse_args, load_config
from common.logger import setup_log, logging
from server.share_server import ShareServer
from client.share_client import ShareClient

logger = None
server = None
client = None

def signal_handler(signum, frame):
    """
    处理 Ctrl+C 中断信号
    确保程序退出时正确关闭连接
    """
    print("\n收到中断信号，正在关闭...")
    if server:
        server.stop()
    if client:
        client.disconnect()
    sys.exit(0)

def main():
    """
    程序主入口

    架构说明：
    - Server（主控端）：监听本地鼠标，将事件发送到 Client
      使用 --server 参数启动
      例如：PyFlow.exe --server --port 12345

    - Client（被控端）：接收事件，在本地执行鼠标操作
      使用 --client 参数启动，连接到主控端
      例如：PyFlow.exe --client --ip 192.168.1.100 --port 12345

    使用场景：
    1. 在你的主控电脑（鼠标连接的电脑）上运行 --server
    2. 在被控电脑上运行 --client，连接到主控电脑的 IP
    3. 当鼠标移出主控电脑屏幕边界时，会跳转到被控电脑
    """
    global logger, server, client

    # 1. 注册 Ctrl+C 信号处理器
    signal.signal(signal.SIGINT, signal_handler)

    # 2. 解析命令行参数
    args = parse_args()

    # 3. 加载配置文件
    config = load_config(args.config if args.config else "config.ini")

    # 4. 初始化日志
    log_file = "server.log" if args.server else "client.log"
    log_level = getattr(logging, config.get("log_level", "INFO"))
    logger = setup_log(log_file, log_level)
    logger.info("=" * 50)
    logger.info("PyFlow 启动")
    logger.info("=" * 50)

    # 5. 根据命令行参数覆盖配置文件中的值
    if args.ip:
        if args.server:
            config["server_ip"] = args.ip
        else:
            config["client_ip"] = args.ip
    if args.port:
        config["server_port"] = args.port
        config["client_port"] = args.port

    # 6. 根据模式启动
    if args.server:
        # 服务端模式（主控端）
        logger.info(f"启动主控端，监听 {config['server_ip']}:{config['server_port']}")
        print(f"PyFlow 主控端启动，监听 {config['server_ip']}:{config['server_port']}")
        print("等待被控端连接...")
        config_path = getattr(args, 'config_layout', None)
        server = ShareServer(config["server_ip"], config["server_port"], config_path)
        if args.remote:
            remote_parts = args.remote.split(':')
            if len(remote_parts) == 3:
                screen_id, host_port = remote_parts[0], remote_parts[1:]
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 12345
                width = int(getattr(args, 'remote_width', 1920))
                height = int(getattr(args, 'remote_height', 1080))
                direction = getattr(args, 'remote_direction', 'right')
                alignment = getattr(args, 'remote_alignment', 'left')
                server.add_remote_screen(screen_id, host, port, width, height, direction, alignment)
        try:
            server.start()
        except Exception as e:
            logger.error(f"服务端运行错误: {e}")
            server.stop()

    elif args.client:
        # 客户端模式（被控端）
        logger.info(f"启动被控端，连接 {config['client_ip']}:{config['client_port']}")
        print(f"PyFlow 被控端启动，连接到 {config['client_ip']}:{config['client_port']}")
        client = ShareClient(config["client_ip"], config["client_port"])
        try:
            if client.connect():
                import time
                while client.connected:
                    time.sleep(1)
            else:
                logger.error("连接主控端失败")
        except Exception as e:
            logger.error(f"客户端运行错误: {e}")
            client.disconnect()
    else:
        print("用法:")
        print("  主控端（在你的电脑上）: PyFlow.exe --server [--port 12345]")
        print("  被控端（在另一台电脑上）: PyFlow.exe --client --ip <主控端IP> [--port 12345]")
        sys.exit(1)

if __name__ == "__main__":
    main()
