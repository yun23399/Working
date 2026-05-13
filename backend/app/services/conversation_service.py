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
from app.schemas.conversation import (
    ChatRequestSchema,
    ConversationCreateSchema,
    ConversationManagerRoleUpdateSchema,
    ConversationManagerStateResponseSchema,
    ManagerProgressSchema,
)
from app.services.workflow_service import create_workflow_preview

BroadcastCallable = Callable[[str, int, dict[str, Any]], Awaitable[None]]


class ConversationNotFoundError(Exception):
    """对话不存在异常，供路由层转换为业务错误响应"""


class ConversationNotReadyToStartError(Exception):
    """总代理尚未完成需求收集时的启动异常"""


def touch_conversation(conversation: Conversation) -> None:
    """刷新对话更新时间，保证历史列表可按最近活跃排序"""

    conversation.updated_at = datetime.now(timezone.utc)


def create_conversation(
    db: Session, current_user: User, payload: ConversationCreateSchema
) -> Conversation:
    """为当前用户创建新对话并持久化到数据库"""

    conversation = Conversation(
        user_id=current_user.id,
        title=payload.title,
        manager_role=payload.manager_role,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def update_conversation_manager_role(
    db: Session,
    conversation: Conversation,
    payload: ConversationManagerRoleUpdateSchema,
) -> Conversation:
    """更新当前对话的总代理角色，供用户在聊天前后切换主导风格"""

    conversation.manager_role = payload.manager_role.strip()
    touch_conversation(conversation)
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


def build_manager_state_response(
    conversation: Conversation,
    history_messages: list[ManagerConversationMessage],
) -> ConversationManagerStateResponseSchema:
    """构造当前对话的总代理准备状态响应"""

    manager_agent = ManagerAgent()
    progress_state = manager_agent.analyze_progress(
        conversation.manager_role,
        conversation.title,
        history_messages,
    )
    return ConversationManagerStateResponseSchema(
        conversation_id=conversation.id,
        title=conversation.title,
        manager_progress=ManagerProgressSchema(
            selected_role=progress_state.selected_role,
            completion_score=progress_state.completion_score,
            readiness_threshold=progress_state.readiness_threshold,
            is_ready_to_start=progress_state.is_ready_to_start,
            missing_slots=progress_state.missing_slots,
            collected_points=progress_state.collected_points,
            suggested_next_questions=progress_state.suggested_next_questions,
            summary=progress_state.summary,
        ),
    )


def get_conversation_manager_state(
    db: Session, conversation: Conversation
) -> ConversationManagerStateResponseSchema:
    """读取当前对话的总代理需求收集进度"""

    history_messages = [
        ManagerConversationMessage(role=message.role, content=message.content)
        for message in list_messages(db, conversation)
    ]
    return build_manager_state_response(conversation, history_messages)


def prepare_workflow_from_manager_state(
    db: Session,
    current_user: User,
    conversation: Conversation,
) -> int:
    """当总代理判断信息足够时，自动生成并确认最新工作流预览"""

    history_messages = [
        ManagerConversationMessage(role=message.role, content=message.content)
        for message in list_messages(db, conversation)
    ]
    manager_state = build_manager_state_response(conversation, history_messages)
    if not manager_state.manager_progress.is_ready_to_start:
        raise ConversationNotReadyToStartError(
            "总代理尚未收集到足够需求信息，请先继续补充任务目标、范围和约束"
        )

    workflow = create_workflow_preview(
        db,
        current_user,
        conversation,
        history_messages,
        pause_after_nodes=[],
    )
    workflow.status = "confirmed"
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow.id


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

        with SessionLocal() as db:
            conversation, history_messages = load_conversation_context(
                db, conversation_id
            )
            manager_state = build_manager_state_response(conversation, history_messages)

        runtime_label = manager_agent.get_runtime_label()
        await broadcaster(
            "log",
            conversation_id,
            {
                "level": "INFO",
                "message": (
                    f"总代理正在通过 {runtime_label} 梳理需求，"
                    f"当前完成度 {manager_state.manager_progress.completion_score}%"
                ),
                "agent_id": "manager",
            },
        )

        stream_result = await stream_tokens_to_websocket(
            conversation_id=conversation_id,
            token_stream=manager_agent.stream_reply(
                conversation.manager_role,
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
            latest_conversation, latest_history_messages = load_conversation_context(
                db, conversation_id
            )
            latest_manager_state = build_manager_state_response(
                latest_conversation,
                latest_history_messages,
            )

        await broadcaster(
            "log",
            conversation_id,
            {
                "level": "INFO",
                "message": latest_manager_state.manager_progress.summary,
                "agent_id": "manager",
            },
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
