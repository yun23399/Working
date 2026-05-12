"""LLM 流式输出处理模块，负责标准化推送 WebSocket 事件"""

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from loguru import logger

BroadcastCallable = Callable[[str, int, dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class StreamResult:
    """流式输出聚合结果，包含完整文本与近似 token 数"""

    content: str
    token_count: int


def estimate_token_count(content: str, chunk_count: int) -> int:
    """基于输出分片数估算 token 数，保证消息元数据可回填"""

    normalized_content = content.strip()
    if not normalized_content:
        return 0
    return max(chunk_count, 1)


async def stream_tokens_to_websocket(
    conversation_id: int,
    token_stream: AsyncIterator[str],
    broadcaster: BroadcastCallable,
    agent_id: str = "manager",
) -> StreamResult:
    """消费 LLM 文本流并向前端持续广播 token 事件"""

    try:
        parts: list[str] = []
        chunk_count = 0
        async for token in token_stream:
            parts.append(token)
            chunk_count += 1
            await broadcaster(
                "token",
                conversation_id,
                {"content": token, "agent_id": agent_id},
            )

        content = "".join(parts).strip()
        return StreamResult(
            content=content,
            token_count=estimate_token_count(content, chunk_count),
        )
    except Exception as exc:
        logger.exception("WebSocket Token 推送失败: {}", exc)
        raise
