"""统一日志系统"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(log_dir: str = None, level: int = logging.INFO) -> logging.Logger:
    """初始化应用日志系统

    Args:
        log_dir: 日志文件目录，为None则仅控制台输出
        level: 日志级别

    Returns:
        根Logger实例
    """
    root_logger = logging.getLogger("labeltorch")
    root_logger.setLevel(level)

    # 避免重复添加handler
    if root_logger.handlers:
        return root_logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件handler（带轮转）
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "labeltorch.log")
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger
