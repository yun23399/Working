"""对话服务层，处理对话、消息与 Manager 流式回复逻辑"""

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.llm.providers import LLMConfigurationError
from app.core.llm.streaming import stream_tokens_to_websocket
from app.core.manager.manager_agent import (
    ManagerAgent,
    ManagerConversationMessage,
)
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


def load_conversation_context(
    db: Session, conversation_id: int
) -> tuple[Conversation, list[ManagerConversationMessage]]:
    """加载对话与完整历史消息，供 Manager 生成真实回复"""

    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(conversation_id)

    history_messages = [
        ManagerConversationMessage(role=message.role, content=message.content)
        for message in list_messages(db, conversation)
    ]
    return conversation, history_messages


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
    broadcaster: BroadcastCallable,
) -> None:
    """生成 Manager 的真实流式回复，并在完成后持久化消息"""

    manager_agent = ManagerAgent()
    try:
        logger.info("开始推送对话 {} 的 Manager 流式回复", conversation_id)
        await broadcaster(
            "agent_status",
            conversation_id,
            {"agent_id": "manager", "status": "running", "role": "manager"},
        )
        runtime_label = manager_agent.get_runtime_label()
        await broadcaster(
            "log",
            conversation_id,
            {
                "level": "INFO",
                "message": f"Manager 正在通过 {runtime_label} 生成回复",
                "agent_id": "manager",
            },
        )

        with SessionLocal() as db:
            conversation, history_messages = load_conversation_context(
                db, conversation_id
            )

        stream_result = await stream_tokens_to_websocket(
            conversation_id=conversation_id,
            token_stream=manager_agent.stream_reply(
                conversation.title,
                history_messages,
            ),
            broadcaster=broadcaster,
            agent_id="manager",
        )
        if not stream_result.content:
            raise ValueError("Manager 未返回有效内容")

        with SessionLocal() as db:
            save_agent_message(
                db,
                conversation_id,
                stream_result.content,
                stream_result.token_count,
            )

        await broadcaster(
            "agent_status",
            conversation_id,
            {"agent_id": "manager", "status": "done", "role": "manager"},
        )
        logger.info("对话 {} 的 Manager 流式回复已完成", conversation_id)
    except LLMConfigurationError as exc:
        logger.exception("对话 {} 的 LLM 配置无效: {}", conversation_id, exc)
        await broadcaster(
            "log",
            conversation_id,
            {
                "level": "ERROR",
                "message": f"LLM 配置无效: {exc}",
                "agent_id": "manager",
            },
        )
        await broadcaster(
            "agent_status",
            conversation_id,
            {"agent_id": "manager", "status": "failed", "role": "manager"},
        )
        await broadcaster(
            "error",
            conversation_id,
            {"message": str(exc), "recoverable": True},
        )
    except Exception as exc:
        logger.exception("对话 {} 的 Manager 流式回复失败: {}", conversation_id, exc)
        await broadcaster(
            "log",
            conversation_id,
            {
                "level": "ERROR",
                "message": f"Manager 执行失败: {exc}",
                "agent_id": "manager",
            },
        )
        await broadcaster(
            "agent_status",
            conversation_id,
            {"agent_id": "manager", "status": "failed", "role": "manager"},
        )
        await broadcaster(
            "error",
            conversation_id,
            {"message": str(exc), "recoverable": True},
        )
