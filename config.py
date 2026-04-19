import configparser
import argparse

DEFAULT_CONFIG = {
    "server_ip": "0.0.0.0",
    "server_port": 12345,
    "client_ip": "127.0.0.1",
    "client_port": 12345,
    "enable_tls": False,
    "screen_width": 1920,
    "screen_height": 1080,
    "reconnect_interval": 3,
    "log_level": "INFO",
}

def load_config(config_file="config.ini"):
    """
    从配置文件加载配置
    :param config_file: 配置文件路径
    :return: 配置字典
    """
    config = DEFAULT_CONFIG.copy()
    parser = configparser.ConfigParser()
    if parser.read(config_file):
        for key in config:
            if parser.has_option("pyflow", key):
                value = parser.get("pyflow", key)
                if key in ("server_port", "client_port", "screen_width", "screen_height", "reconnect_interval"):
                    config[key] = int(value)
                elif key == "enable_tls":
                    config[key] = value.lower() in ("true", "1", "yes")
                else:
                    config[key] = value
    return config

def parse_args():
    """
    解析命令行参数
    :return: argparse.Namespace 对象
    """
    parser = argparse.ArgumentParser(description="PyFlow - 键盘鼠标共享工具")
    parser.add_argument("--server", action="store_true", help="启动服务端模式")
    parser.add_argument("--client", action="store_true", help="启动客户端模式")
    parser.add_argument("--ip", type=str, help="服务器IP")
    parser.add_argument("--port", type=int, help="端口号")
    parser.add_argument("--config", type=str, default="config.ini", help="配置文件路径")
    parser.add_argument("--config-layout", type=str, default=None, help="屏幕布局配置文件路径")
    parser.add_argument("--remote", type=str, help="远程屏幕配置，格式: screen_id:host:port")
    parser.add_argument("--remote-width", type=int, default=1920, help="远程屏幕宽度")
    parser.add_argument("--remote-height", type=int, default=1080, help="远程屏幕高度")
    parser.add_argument("--remote-direction", type=str, default="right", choices=["left", "right", "top", "bottom"], help="远程屏幕方向")
    parser.add_argument("--remote-alignment", type=str, default="left", choices=["left", "right", "top", "bottom"], help="远程屏幕对齐方式")
    return parser.parse_args()

def get_config(key=None, config_dict=None):
    """
    获取指定配置项
    :param key: 配置项名称，如果为 None 则返回全部配置
    :param config_dict: 配置字典，默认为 DEFAULT_CONFIG
    :return: 配置值或配置字典
    """
    if config_dict is None:
        config_dict = DEFAULT_CONFIG
    if key is None:
        return config_dict
    return config_dict.get(key)

if __name__ == "__main__":
    args = parse_args()
    config = load_config(args.config)
    if args.ip:
        config["client_ip"] = args.ip
    if args.port:
        config["client_port"] = args.port
        config["server_port"] = args.port
    print("当前配置:", config)