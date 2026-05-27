"""
DeepSeek API 客户端
提供异步的文本增强功能
"""
import httpx
from typing import Optional
from loguru import logger


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        timeout: int = 30
    ):
        """
        初始化 DeepSeek 客户端

        Args:
            api_key: DeepSeek API Key
            base_url: API 基础 URL
            model: 使用的模型名称
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def enhance_text(self, text: str, prompt_template: str) -> str:
        """
        调用 DeepSeek API 增强文本

        Args:
            text: 原始文本
            prompt_template: Prompt 模板（system 消息）

        Returns:
            处理后的文本

        Raises:
            httpx.HTTPError: HTTP 请求失败
            ValueError: API 返回格式错误
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        logger.info(f"准备调用 API，原文长度: {len(text)} 字符")

        messages = [
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": text}
        ]

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            response.raise_for_status()
            result = response.json()

            if "choices" not in result or not result["choices"]:
                raise ValueError("API 返回格式错误: 缺少 choices 字段")

            enhanced_text = result["choices"][0]["message"]["content"]
            logger.info(f"API 调用成功，结果长度: {len(enhanced_text)} 字符")

            return enhanced_text

        except httpx.TimeoutException as e:
            logger.error(f"API 请求超时: {e}")
            raise Exception("API 请求超时，请检查网络连接")
        except httpx.HTTPStatusError as e:
            logger.error(f"API 返回错误状态码: {e.response.status_code}")
            raise Exception(f"API 调用失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"API 调用异常: {e}")
            raise

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
