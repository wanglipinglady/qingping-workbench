"""
MiniMax API 客户端封装
支持对话补全、流式对话和 Embedding 向量化
"""
import json
import time
from typing import List, Dict, Any, Optional, Generator

import requests

from app.core.config import settings


class MiniMaxClient:
    """MiniMax API 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        chat_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        初始化 MiniMax 客户端

        Args:
            api_key: API 密钥，默认从配置读取
            base_url: API 基础地址，默认从配置读取
            chat_model: 对话模型名称，默认从配置读取
            embedding_model: Embedding 模型名称，默认从配置读取
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.api_key = api_key or settings.MINIMAX_API_KEY
        self.base_url = base_url or settings.MINIMAX_BASE_URL
        self.chat_model = chat_model or settings.MINIMAX_CHAT_MODEL
        self.embedding_model = embedding_model or settings.MINIMAX_EMBEDDING_MODEL
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 通用请求头
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """
        带重试机制的请求

        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 其他请求参数

        Returns:
            响应对象

        Raises:
            Exception: 重试后仍然失败
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, timeout=60, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                continue
        raise last_exception  # type: ignore

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        对话补全（非流式）

        Args:
            messages: 对话消息列表，格式为 [{"role": "user", "content": "你好"}, ...]
            model: 模型名称，默认使用配置的模型
            temperature: 采样温度
            top_p: 核采样参数
            max_tokens: 最大生成 token 数
            stream: 是否流式输出（此方法始终返回完整结果）
            **kwargs: 其他传递给 API 的参数

        Returns:
            完整的 API 响应字典

        Raises:
            Exception: API 调用失败时抛出
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model or self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }
        payload.update(kwargs)

        try:
            response = self._request_with_retry(
                "POST", url, headers=self._headers, json=payload
            )
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"MiniMax 对话 API 调用失败: {e}") from e

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Generator[str, None, None]:
        """
        流式对话（SSE 格式）

        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 采样温度
            top_p: 核采样参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Yields:
            SSE 格式的数据字符串

        Raises:
            Exception: API 调用失败时抛出
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model or self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": True,
        }
        payload.update(kwargs)

        try:
            response = requests.post(
                url,
                headers=self._headers,
                json=payload,
                stream=True,
                timeout=60,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    # SSE 格式: data: {...}
                    if line_str.startswith("data:"):
                        data_str = line_str[5:].strip()
                        if data_str == "[DONE]":
                            break
                        yield data_str
        except requests.RequestException as e:
            raise Exception(f"MiniMax 流式对话 API 调用失败: {e}") from e

    def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs,
    ) -> List[List[float]]:
        """
        文本向量化（Embedding）

        Args:
            texts: 待向量化的文本列表
            model: Embedding 模型名称，默认使用配置的模型
            **kwargs: 其他参数

        Returns:
            向量列表，每个文本对应一个浮点向量

        Raises:
            Exception: API 调用失败时抛出
        """
        if not texts:
            return []

        url = f"{self.base_url}/embeddings"
        payload = {
            "model": model or self.embedding_model,
            "texts": texts,
        }
        payload.update(kwargs)

        try:
            response = self._request_with_retry(
                "POST", url, headers=self._headers, json=payload
            )
            result = response.json()
            # 解析向量结果
            # 不同 API 返回格式可能略有不同，此处做兼容处理
            if "data" in result:
                embeddings = []
                for item in result["data"]:
                    if "embedding" in item:
                        embeddings.append(item["embedding"])
                return embeddings
            elif "vectors" in result:
                return result["vectors"]
            else:
                raise Exception(f"无法解析 Embedding 响应: {result}")
        except requests.RequestException as e:
            raise Exception(f"MiniMax Embedding API 调用失败: {e}") from e

    def get_chat_reply(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """
        便捷方法：获取对话回复的纯文本内容

        Args:
            messages: 对话消息列表
            **kwargs: 其他参数

        Returns:
            回复文本
        """
        result = self.chat(messages, **kwargs)
        # 解析回复内容
        try:
            content = ""
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
                elif "text" in choice:
                    content = choice["text"]
            # 过滤掉 MiniMax M2.7/M3 模型的 <think> 推理过程标签
            content = self._strip_think_tags(content)
            return content
        except Exception:
            return ""

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        """
        移除 MiniMax M2.7/M3 模型输出的 <think>...</think> 推理过程标签
        """
        if not text:
            return text
        import re
        # 移除 <think> 及其内容（包括跨行的情况）
        result = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return result.strip()


# 全局 MiniMax 客户端实例
minimax_client = MiniMaxClient()
