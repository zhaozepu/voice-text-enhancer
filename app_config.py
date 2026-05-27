"""
应用配置路径管理
处理打包后的配置文件路径
"""
import os
import sys
from pathlib import Path
import shutil


def get_app_path():
    """获取应用程序路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        return Path(sys._MEIPASS)
    else:
        # 开发环境路径
        return Path(__file__).parent


def get_user_config_dir():
    """获取用户配置目录"""
    config_dir = Path.home() / '.voice-text-enhancer'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file():
    """
    获取配置文件路径
    优先使用用户目录的配置，如果不存在则从应用包中复制
    """
    user_config_dir = get_user_config_dir()
    user_config_file = user_config_dir / 'config.yaml'

    if not user_config_file.exists():
        # 从应用包中复制示例配置
        app_path = get_app_path()
        example_config = app_path / 'config.example.yaml'

        if example_config.exists():
            shutil.copy(example_config, user_config_file)
            print(f"已创建配置文件: {user_config_file}")
        else:
            raise FileNotFoundError(
                f"配置文件不存在: {user_config_file}\n"
                f"请手动创建配置文件或重新安装应用"
            )

    return str(user_config_file)


def get_env_file():
    """
    获取环境变量文件路径
    优先使用用户目录的 .env，如果不存在则从应用包中复制
    """
    user_config_dir = get_user_config_dir()
    user_env_file = user_config_dir / '.env'

    if not user_env_file.exists():
        # 从应用包中复制示例
        app_path = get_app_path()
        example_env = app_path / '.env.example'

        if example_env.exists():
            shutil.copy(example_env, user_env_file)
            print(f"已创建环境变量文件: {user_env_file}")
        else:
            # 如果示例文件不存在，创建空文件
            user_env_file.touch()

    return str(user_env_file)


def initialize_config():
    """
    初始化配置
    确保所有必要的配置文件都存在
    """
    config_file = get_config_file()
    env_file = get_env_file()

    print(f"配置文件: {config_file}")
    print(f"环境变量: {env_file}")

    return config_file, env_file
