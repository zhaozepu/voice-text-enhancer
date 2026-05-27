"""
文本处理器测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.text_processor import TextProcessor
from src.api.deepseek_client import DeepSeekClient


@pytest.fixture
def mock_api_client():
    """创建模拟的 API 客户端"""
    client = AsyncMock(spec=DeepSeekClient)
    client.enhance_text = AsyncMock(return_value="这是处理后的文本")
    return client


@pytest.fixture
def config():
    """测试配置"""
    return {
        'prompts': {
            'test': '测试 prompt'
        },
        'active_prompt': 'test',
        'notifications': {
            'show_processing': False,
            'show_completion': False,
            'show_errors': False
        }
    }


def test_text_processor_init(mock_api_client, config):
    """测试文本处理器初始化"""
    processor = TextProcessor(mock_api_client, config)

    assert processor.api_client == mock_api_client
    assert processor.config == config
    assert processor._processing is False


@pytest.mark.asyncio
async def test_enhance_text(mock_api_client, config):
    """测试文本增强"""
    processor = TextProcessor(mock_api_client, config)

    result = await processor._enhance_text("测试文本")

    assert result == "这是处理后的文本"
    mock_api_client.enhance_text.assert_called_once()
