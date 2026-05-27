"""
用户配置管理：API Key、模式等
统一保存到 ~/.voice-text-enhancer/
"""
import os
from pathlib import Path
from typing import Optional


def get_user_dir() -> Path:
    """用户配置目录"""
    d = Path.home() / '.voice-text-enhancer'
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_env_file() -> Path:
    return get_user_dir() / '.env'


def read_api_key() -> str:
    """从 ~/.voice-text-enhancer/.env 读取 DEEPSEEK_API_KEY"""
    env = get_env_file()
    if not env.exists():
        return ''
    try:
        for line in env.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                if k.strip() == 'DEEPSEEK_API_KEY':
                    return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return ''


def write_api_key(api_key: str) -> bool:
    """写入 API Key 到 ~/.voice-text-enhancer/.env"""
    env = get_env_file()
    api_key = api_key.strip()
    try:
        lines = []
        found = False
        if env.exists():
            for line in env.read_text(encoding='utf-8').splitlines():
                if line.strip().startswith('DEEPSEEK_API_KEY='):
                    lines.append(f'DEEPSEEK_API_KEY={api_key}')
                    found = True
                else:
                    lines.append(line)
        if not found:
            if lines and lines[-1].strip():
                lines.append('')
            lines.append('# DeepSeek API Key')
            lines.append(f'DEEPSEEK_API_KEY={api_key}')
        env.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        os.chmod(env, 0o600)  # 仅当前用户可读
        return True
    except Exception:
        return False


def has_api_key() -> bool:
    """是否已配置 API Key"""
    key = read_api_key()
    return bool(key) and key != 'sk-your-api-key-here' and key.startswith('sk-')
