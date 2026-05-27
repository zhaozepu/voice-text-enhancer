"""
日志工具
配置 loguru 日志记录
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(config: dict):
    """
    配置日志系统

    Args:
        config: 配置字典，包含 logging 部分
    """
    logger.remove()

    log_level = config.get('logging', {}).get('level', 'INFO')

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    log_file = config.get('logging', {}).get('file', '~/.voice-text-enhancer/app.log')
    log_file_path = Path(log_file).expanduser()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )

    logger.info(f"日志系统初始化完成，级别: {log_level}")
    logger.info(f"日志文件: {log_file_path}")
