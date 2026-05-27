"""
配置加载器
从 YAML 文件和环境变量加载配置
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str = "config.yaml", env_path: str = ".env"):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径
            env_path: 环境变量文件路径
        """
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)

    def load(self) -> Dict[str, Any]:
        """
        加载配置

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误或缺少必需字段
        """
        load_dotenv(self.env_path)

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}\n"
                f"请复制 config.example.yaml 为 config.yaml 并进行配置"
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")

        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError(
                "未找到 DEEPSEEK_API_KEY 环境变量\n"
                "请在 .env 文件中设置 DEEPSEEK_API_KEY"
            )

        if 'api' not in config:
            config['api'] = {}
        config['api']['key'] = api_key

        self._validate_config(config)

        logger.info("配置加载成功")
        return config

    def _validate_config(self, config: Dict[str, Any]):
        """
        验证配置

        Args:
            config: 配置字典

        Raises:
            ValueError: 配置不完整或格式错误
        """
        required_keys = ['api', 'hotkey', 'prompts', 'active_prompt']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置缺少必需字段: {key}")

        if 'trigger' not in config['hotkey']:
            raise ValueError("配置缺少 hotkey.trigger 字段")

        active_prompt = config['active_prompt']
        if active_prompt not in config['prompts']:
            raise ValueError(
                f"active_prompt '{active_prompt}' 在 prompts 中不存在"
            )

        logger.debug("配置验证通过")
