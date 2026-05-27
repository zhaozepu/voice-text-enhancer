"""
API 客户端测试
"""
import pytest
import os
from dotenv import load_dotenv
from src.api.deepseek_client import DeepSeekClient


load_dotenv()


@pytest.fixture
def api_client():
    """创建 API 客户端"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key or api_key == 'sk-your-api-key-here':
        pytest.skip("需要配置 DEEPSEEK_API_KEY 才能运行此测试")

    return DeepSeekClient(api_key=api_key)


@pytest.mark.asyncio
async def test_enhance_text_basic(api_client):
    """测试基本的文本增强功能"""
    text = "这是测试文本有一些错别字"
    prompt = "纠正文本中的错误，直接返回修正后的文本"

    result = await api_client.enhance_text(text, prompt)

    assert result is not None
    assert len(result) > 0
    assert result != text  # 应该有变化

    await api_client.close()


@pytest.mark.asyncio
async def test_enhance_empty_text(api_client):
    """测试空文本"""
    with pytest.raises(ValueError):
        await api_client.enhance_text("", "test prompt")

    await api_client.close()


@pytest.mark.asyncio
async def test_api_timeout():
    """测试 API 超时"""
    client = DeepSeekClient(
        api_key="invalid-key",
        timeout=1
    )

    with pytest.raises(Exception):
        await client.enhance_text("test", "prompt")

    await client.close()
