"""LLM 统一适配器，负责通过 LiteLLM 调用不同提供商"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx
from litellm import acompletion
from loguru import logger

from app.core.llm.providers import (
    LLMConfigurationError,
    LLMProviderConfig,
    resolve_provider_config,
    split_provider_prefixed_model,
)


class LLMRequestError(Exception):
    """LLM 请求异常，用于向上层返回统一错误语义"""


@dataclass(frozen=True)
class ChatMessage:
    """对话消息结构，供统一适配层接收历史上下文"""

    role: str
    content: str


def get_mapping_value(source: Any, key: str) -> Any:
    """兼容对象与字典两种访问方式，读取指定字段值"""

    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def extract_text_from_chunk(chunk: Any) -> str:
    """从 LiteLLM 流式分片中提取文本内容，兼容多种返回结构"""

    choices = get_mapping_value(chunk, "choices")
    if not choices:
        return ""

    first_choice = choices[0]
    delta = get_mapping_value(first_choice, "delta")
    content = get_mapping_value(delta, "content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            # 兼容富文本分片结构，优先拼接 text 字段
            text_value = get_mapping_value(item, "text")
            if isinstance(text_value, str) and text_value:
                parts.append(text_value)
        return "".join(parts)

    text = get_mapping_value(first_choice, "text")
    if isinstance(text, str):
        return text
    return ""


class LLMAdapter:
    """LLM 统一适配器，屏蔽不同提供商的调用差异"""

    def __init__(self, provider_config: LLMProviderConfig | None = None) -> None:
        """初始化适配器，可显式注入运行配置用于测试或扩展"""

        self.provider_config = provider_config

    def get_active_config(self) -> LLMProviderConfig:
        """返回当前生效的 LLM 配置，供上层记录日志与调试"""

        return self.provider_config or resolve_provider_config()

    def get_runtime_label(self) -> str:
        """生成当前模型标识文本，便于日志展示使用中的模型"""

        config = self.get_active_config()
        _, model_name = split_provider_prefixed_model(config.model)
        return f"{config.provider}::{model_name}"

    def serialize_messages(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        """将内部消息对象序列化为 LiteLLM 所需的请求结构"""

        return [
            {"role": message.role, "content": message.content} for message in messages
        ]

    async def stream_ollama_chat(
        self,
        config: LLMProviderConfig,
        messages: list[ChatMessage],
    ) -> AsyncIterator[str]:
        """通过 Ollama 原生聊天接口流式生成文本，规避当前 LiteLLM 流式兼容问题"""

        try:
            _, model_name = split_provider_prefixed_model(config.model)
            request_body = {
                "model": model_name,
                "messages": self.serialize_messages(messages),
                "stream": True,
            }
            url = f"{config.base_url}/api/chat"

            async with httpx.AsyncClient(
                trust_env=False,
                timeout=config.timeout_seconds,
            ) as client:
                async with client.stream("POST", url, json=request_body) as response:
                    if response.status_code != 200:
                        response_body = await response.aread()
                        error_detail = response_body.decode("utf-8", errors="ignore")
                        raise LLMRequestError(
                            f"Ollama 请求失败: {response.status_code} {error_detail}"
                        )

                    async for raw_line in response.aiter_lines():
                        if not raw_line:
                            continue

                        try:
                            chunk = json.loads(raw_line)
                        except json.JSONDecodeError as exc:
                            raise LLMRequestError(
                                f"Ollama 流式响应解析失败: {exc}"
                            ) from exc

                        if not isinstance(chunk, dict):
                            continue

                        content = chunk.get("message", {}).get("content", "")
                        if isinstance(content, str) and content:
                            yield content
        except LLMRequestError:
            raise
        except Exception as exc:
            logger.exception("Ollama 原生流式请求失败: {}", exc)
            raise LLMRequestError(str(exc)) from exc

    async def stream_chat(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        """发起统一的流式对话请求，并逐段产出文本内容"""

        config = self.get_active_config()
        try:
            logger.info("开始调用 LLM：{}", self.get_runtime_label())
            if config.provider == "ollama":
                async for token in self.stream_ollama_chat(config, messages):
                    yield token
                return

            request_messages = self.serialize_messages(messages)
            response = await acompletion(
                model=config.model,
                messages=request_messages,
                stream=True,
                timeout=config.timeout_seconds,
                api_key=config.api_key,
                base_url=config.base_url,
            )
            async for chunk in response:
                text = extract_text_from_chunk(chunk)
                if text:
                    yield text
        except LLMConfigurationError:
            raise
        except LLMRequestError:
            raise
        except Exception as exc:
            logger.exception("LLM 请求失败: {}", exc)
            raise LLMRequestError(str(exc)) from exc
