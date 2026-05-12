"""对话服务层，处理对话、消息与模拟流式回复逻辑"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import ChatRequestSchema, ConversationCreateSchema

BroadcastCallable = Callable[[str, int, dict[str, Any]], Awaitable[None]]


class ConversationNotFoundError(Exception):
    """对话不存在异常，供路由层转换为业务错误响应"""


def touch_conversation(conversation: Conversation) -> None:
    """刷新对话更新时间，保证历史列表可按最近活跃排序"""

    conversation.updated_at = datetime.now(timezone.utc)


def create_conversation(
    db: Session, current_user: User, payload: ConversationCreateSchema
) -> Conversation:
    """为当前用户创建新对话并持久化到数据库"""

    conversation = Conversation(user_id=current_user.id, title=payload.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(db: Session, current_user: User) -> list[Conversation]:
    """返回当前用户的对话列表，按更新时间倒序排列"""

    statement = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(db.scalars(statement).all())


def get_conversation_by_owner(
    db: Session, conversation_id: int, current_user: User
) -> Conversation:
    """根据用户归属查询对话，不存在时抛出业务异常"""

    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    conversation = db.scalar(statement)
    if conversation is None:
        raise ConversationNotFoundError(conversation_id)
    return conversation


def list_messages(db: Session, conversation: Conversation) -> list[Message]:
    """返回指定对话的消息列表，按创建顺序排序"""

    statement = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    return list(db.scalars(statement).all())


def create_user_message(
    db: Session, conversation: Conversation, payload: ChatRequestSchema
) -> Message:
    """将用户发送的消息保存到数据库，供后续流式回复使用"""

    touch_conversation(conversation)
    message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.content,
        token_count=len(payload.content.split()),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def build_manager_reply(prompt: str) -> str:
    """根据用户输入生成阶段一的模拟 Manager 回复文本"""

    if "商品" in prompt or "页面" in prompt:
        return (
            "我已经收到你的需求。下一步我会先整理页面结构、关键交互和展示区域，"
            "随后再进入工作流规划。当前阶段先为你建立最小对话闭环。"
        )
    return (
        "需求已收到。当前系统正在使用模拟流式回复验证聊天链路，"
        "后续会替换为真实的 LLM 输出。"
    )


def split_reply_for_streaming(reply: str, chunk_size: int = 12) -> list[str]:
    """将回复切分为多个短片段，兼容中文文本的流式展示"""

    return [
        reply[index : index + chunk_size]
        for index in range(0, len(reply), chunk_size)
        if reply[index : index + chunk_size]
    ]


def save_agent_message(
    db: Session, conversation_id: int, content: str, token_count: int
) -> Message:
    """将 Manager 回复保存到数据库，并返回写入后的消息对象"""

    conversation = db.get(Conversation, conversation_id)
    if conversation is not None:
        touch_conversation(conversation)
    message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=content,
        token_count=token_count,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


async def stream_manager_reply(
    conversation_id: int,
    prompt: str,
    broadcaster: BroadcastCallable,
) -> None:
    """使用模拟流式回复验证阶段一聊天链路，并将消息持久化"""

    try:
        logger.info("开始推送对话 {} 的模拟流式回复", conversation_id)
        await broadcaster(
            "agent_status",
            conversation_id,
            {"agent_id": "manager", "status": "running", "role": "manager"},
        )
        await broadcaster(
            "log",
            conversation_id,
            {
                "level": "INFO",
                "message": "Manager 正在生成模拟流式回复",
                "agent_id": "manager",
            },
        )

        reply = build_manager_reply(prompt)
        chunks = split_reply_for_streaming(reply)
        token_count = 0
        for chunk in chunks:
            token_count += 1
            await broadcaster(
                "token",
                conversation_id,
                {"content": chunk, "agent_id": "manager"},
            )
            await asyncio.sleep(0.08)

        with SessionLocal() as db:
            save_agent_message(db, conversation_id, reply, token_count)

        await broadcaster(
            "agent_status",
            conversation_id,
            {"agent_id": "manager", "status": "done", "role": "manager"},
        )
        logger.info("对话 {} 的模拟流式回复已完成", conversation_id)
    except Exception as exc:
        logger.exception("对话 {} 的模拟流式回复失败: {}", conversation_id, exc)
        await broadcaster(
            "error",
            conversation_id,
            {"message": str(exc), "recoverable": True},
        )
