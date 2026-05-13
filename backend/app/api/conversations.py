"""对话路由模块，提供对话创建、查询与总代理聊天接口"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.ws import connection_manager
from app.models.user import User
from app.schemas.conversation import (
    ChatAcceptedSchema,
    ChatRequestSchema,
    ConversationCreateSchema,
    ConversationManagerRoleUpdateSchema,
    ConversationManagerStateResponseSchema,
    ConversationResponseSchema,
    MessageResponseSchema,
)
from app.schemas.workflow import WorkflowPreviewResponseSchema
from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationNotReadyToStartError,
    create_conversation,
    create_user_message,
    get_conversation_by_owner,
    get_conversation_manager_state,
    list_conversations,
    list_messages,
    prepare_workflow_from_manager_state,
    stream_manager_reply,
    update_conversation_manager_role,
)
from app.services.workflow_service import get_workflow_by_id, workflow_to_response

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponseSchema])
def get_conversation_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationResponseSchema]:
    """返回当前用户的对话列表，供前端侧边栏加载历史记录"""

    try:
        conversations = list_conversations(db, current_user)
        return [
            ConversationResponseSchema.model_validate(item) for item in conversations
        ]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "获取对话列表失败",
                "code": "LIST_CONVERSATIONS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "",
    response_model=ConversationResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation_endpoint(
    payload: ConversationCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponseSchema:
    """创建新对话并返回基础信息，用于进入聊天流程"""

    try:
        conversation = create_conversation(db, current_user, payload)
        return ConversationResponseSchema.model_validate(conversation)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "创建对话失败",
                "code": "CREATE_CONVERSATION_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get(
    "/{conversation_id}/manager-state",
    response_model=ConversationManagerStateResponseSchema,
)
def get_conversation_manager_state_endpoint(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationManagerStateResponseSchema:
    """返回当前对话的总代理需求收集进度与可开始状态"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        return get_conversation_manager_state(db, conversation)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "读取总代理状态失败",
                "code": "GET_MANAGER_STATE_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get("/{conversation_id}/messages", response_model=list[MessageResponseSchema])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageResponseSchema]:
    """返回对话历史消息，供聊天页加载初始内容"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        messages = list_messages(db, conversation)
        return [MessageResponseSchema.model_validate(item) for item in messages]
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "获取消息失败",
                "code": "LIST_MESSAGES_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.put(
    "/{conversation_id}/manager-role", response_model=ConversationResponseSchema
)
def update_conversation_manager_role_endpoint(
    conversation_id: int,
    payload: ConversationManagerRoleUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponseSchema:
    """更新当前对话使用的总代理角色"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        updated_conversation = update_conversation_manager_role(
            db, conversation, payload
        )
        return ConversationResponseSchema.model_validate(updated_conversation)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "更新总代理角色失败",
                "code": "UPDATE_MANAGER_ROLE_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post("/{conversation_id}/chat", response_model=ChatAcceptedSchema)
async def chat_with_manager(
    conversation_id: int,
    payload: ChatRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatAcceptedSchema:
    """接收用户消息并触发 Manager 真实流式回复任务"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        message = create_user_message(db, conversation, payload)
        asyncio.create_task(
            stream_manager_reply(
                conversation.id,
                connection_manager.broadcast,
            )
        )
        return ChatAcceptedSchema(
            message_id=message.id,
            conversation_id=conversation.id,
            accepted=True,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "发送消息失败",
                "code": "CHAT_REQUEST_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/{conversation_id}/start-task",
    response_model=WorkflowPreviewResponseSchema,
)
def start_task_from_manager_endpoint(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowPreviewResponseSchema:
    """在总代理确认需求足够后，生成并确认最新工作流预览"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow_id = prepare_workflow_from_manager_state(
            db,
            current_user,
            conversation,
        )
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        return workflow_to_response(workflow)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except ConversationNotReadyToStartError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "总代理尚未完成需求收集",
                "code": "MANAGER_NOT_READY",
                "detail": str(exc),
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "开始任务失败",
                "code": "START_TASK_FAILED",
                "detail": str(exc),
            },
        ) from exc
