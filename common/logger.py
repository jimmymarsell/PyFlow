import logging
import os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name):
    """
    获取一个 logger 实例
    :param name: logger 名称
    :return: logging.Logger 实例
    """
    return logging.getLogger(name)

def setup_log(log_file=None, level=logging.INFO):
    """
    配置日志（输出到文件和控制台）
    :param log_file: 日志文件名
    :param level: 日志级别
    :return: 配置好的 logger 实例
    """
    logger = get_logger(__name__)
    logger.setLevel(level)
    logger.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    if log_file:
        filename = os.path.join(LOG_DIR, f"{timestamp}_{log_file}")
    else:
        filename = os.path.join(LOG_DIR, f"{timestamp}.log")
    file_handler = logging.FileHandler(filename, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

if __name__ == "__main__":
    logger = setup_log("test.log", logging.DEBUG)
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")