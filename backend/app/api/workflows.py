"""工作流路由模块，提供预览生成、查询、确认与执行接口"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.database import SessionLocal
from app.models.conversation import Conversation
from app.models.user import User
from app.models.workflow import Workflow
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
    mark_workflow_running,
    workflow_to_response,
)
from app.workflow.dag_orchestrator import DagOrchestrator, WorkflowExecutionError

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


async def run_workflow_execution_async(workflow_id: int) -> None:
    """后台执行已确认工作流，避免阻塞当前 HTTP 请求"""

    orchestrator = DagOrchestrator()
    with SessionLocal() as db:
        workflow = db.get(Workflow, workflow_id)
        if workflow is None:
            return

        conversation = db.get(Conversation, workflow.conversation_id)
        if conversation is None:
            return

        try:
            await orchestrator.execute(db, workflow, conversation)
        except WorkflowExecutionError:
            return


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


@router.post(
    "/{conversation_id}/{workflow_id}/execute",
    response_model=WorkflowPreviewResponseSchema,
)
async def execute_workflow_endpoint(
    conversation_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowPreviewResponseSchema:
    """启动已确认工作流的最小串行执行链路"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        if workflow.status not in {"confirmed", "completed", "failed"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "工作流状态不允许执行",
                    "code": "INVALID_WORKFLOW_STATUS",
                    "detail": f"当前状态 `{workflow.status}` 不允许启动执行",
                },
            )

        running_workflow = mark_workflow_running(db, workflow)
        asyncio.create_task(run_workflow_execution_async(running_workflow.id))
        return workflow_to_response(running_workflow)
    except WorkflowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流预览不存在",
                "code": "WORKFLOW_NOT_FOUND",
                "detail": f"工作流 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "启动工作流执行失败",
                "code": "EXECUTE_WORKFLOW_FAILED",
                "detail": str(exc),
            },
        ) from exc
