"""工作流路由模块，提供预览生成、查询与确认接口"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.workflow import (
    WorkflowPreviewRequestSchema,
    WorkflowPreviewResponseSchema,
)
from app.services.conversation_service import (
    get_conversation_by_owner,
    load_conversation_context,
)
from app.services.workflow_service import (
    WorkflowNotFoundError,
    confirm_workflow_preview,
    create_workflow_preview,
    get_workflow_by_id,
    list_workflows_by_conversation,
    workflow_to_response,
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get(
    "/{conversation_id}",
    response_model=list[WorkflowPreviewResponseSchema],
)
def get_workflow_list(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkflowPreviewResponseSchema]:
    """返回指定对话下的工作流预览列表，供前端恢复显示"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflows = list_workflows_by_conversation(db, conversation.id)
        return [workflow_to_response(item) for item in workflows]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "获取工作流预览失败",
                "code": "LIST_WORKFLOWS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/{conversation_id}/preview",
    response_model=WorkflowPreviewResponseSchema,
)
def create_workflow_preview_endpoint(
    conversation_id: int,
    payload: WorkflowPreviewRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowPreviewResponseSchema:
    """为指定对话生成或刷新工作流预览"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        existing_workflows = list_workflows_by_conversation(db, conversation.id)
        if existing_workflows and not payload.force_replan:
            return workflow_to_response(existing_workflows[0])

        _, history_messages = load_conversation_context(db, conversation.id)
        workflow = create_workflow_preview(db, conversation, history_messages)
        return workflow_to_response(workflow)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "生成工作流预览失败",
                "code": "CREATE_WORKFLOW_PREVIEW_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/{conversation_id}/{workflow_id}/confirm",
    response_model=WorkflowPreviewResponseSchema,
)
def confirm_workflow_preview_endpoint(
    conversation_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowPreviewResponseSchema:
    """确认指定工作流预览，为后续阶段执行保留状态"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        updated_workflow = confirm_workflow_preview(db, workflow)
        return workflow_to_response(updated_workflow)
    except WorkflowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流预览不存在",
                "code": "WORKFLOW_NOT_FOUND",
                "detail": f"工作流 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "确认工作流预览失败",
                "code": "CONFIRM_WORKFLOW_FAILED",
                "detail": str(exc),
            },
        ) from exc
