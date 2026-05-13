"""日志模块，负责配置 loguru 输出到控制台与文件"""

import sys

from loguru import logger

from app.config import settings


def configure_logger() -> None:
    """初始化日志输出规则，并创建本地日志目录"""

    log_dir = settings.log_dir_path
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        colorize=True,
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        enqueue=True,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
            "{name}:{function}:{line} | {message}"
        ),
    )


def get_logger():
    """返回全局 logger 实例，供业务模块统一记录日志"""

    return logger
