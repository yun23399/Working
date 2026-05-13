"""工作流路由模块，提供预览生成、查询、确认、产物访问与执行接口"""

import asyncio
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.runtime.workflow_concurrency import workflow_concurrency_controller
from app.database import SessionLocal
from app.models.conversation import Conversation
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.workflow import (
    WorkflowArtifactSchema,
    WorkflowControlRequestSchema,
    WorkflowPreviewRequestSchema,
    WorkflowPreviewResponseSchema,
    WorkflowRuntimeLogSchema,
)
from app.services.conversation_service import (
    ConversationNotFoundError,
    get_conversation_by_owner,
    load_conversation_context,
)
from app.services.workflow_artifact_service import (
    InvalidWorkflowArtifactPathError,
    WorkflowArtifactNotFoundError,
    list_workflow_artifacts,
    resolve_workflow_artifact_path,
)
from app.services.workflow_export_service import (
    EmptyArtifactExportError,
    InvalidArtifactExportPathError,
    export_workflow_artifacts_archive,
)
from app.services.workflow_runtime_log_service import list_workflow_runtime_logs
from app.services.workflow_service import (
    WorkflowNotFoundError,
    confirm_workflow_preview,
    create_workflow_preview,
    get_workflow_by_id,
    list_workflows_by_conversation,
    mark_workflow_running,
    workflow_to_response,
)
from app.workflow.checkpoint import (
    WorkflowCheckpointController,
    WorkflowRunNotFoundError,
)
from app.workflow.dag_orchestrator import DagOrchestrator, WorkflowExecutionError

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
checkpoint_controller = WorkflowCheckpointController()


async def run_workflow_execution_async(workflow_id: int) -> None:
    """后台执行已确认工作流，避免阻塞当前 HTTP 请求"""

    orchestrator = DagOrchestrator()
    try:
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
    finally:
        workflow_concurrency_controller.release_slot(workflow_id)


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
                "error": "获取工作流预览失败",
                "code": "LIST_WORKFLOWS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get(
    "/{conversation_id}/{workflow_id}/artifacts",
    response_model=list[WorkflowArtifactSchema],
)
def get_workflow_artifacts_endpoint(
    conversation_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkflowArtifactSchema]:
    """返回指定工作流的真实产物列表，供前端选择预览目标"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        return list_workflow_artifacts(workflow)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "获取工作流产物失败",
                "code": "LIST_WORKFLOW_ARTIFACTS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get("/{conversation_id}/{workflow_id}/artifacts/file")
def get_workflow_artifact_file_endpoint(
    conversation_id: int,
    workflow_id: int,
    path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """返回指定工作流的单个真实产物文件，供前端读取文本或图片内容"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        artifact_path = resolve_workflow_artifact_path(workflow, path)
        media_type = (
            mimetypes.guess_type(artifact_path.name)[0] or "application/octet-stream"
        )
        return FileResponse(
            path=artifact_path,
            media_type=media_type,
            filename=artifact_path.name,
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
    except WorkflowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流预览不存在",
                "code": "WORKFLOW_NOT_FOUND",
                "detail": f"工作流 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except InvalidWorkflowArtifactPathError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "工作流产物路径不合法",
                "code": "INVALID_WORKFLOW_ARTIFACT_PATH",
                "detail": str(exc),
            },
        ) from exc
    except WorkflowArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流产物不存在",
                "code": "WORKFLOW_ARTIFACT_NOT_FOUND",
                "detail": f"产物 `{exc}` 不存在或尚未生成",
            },
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "读取工作流产物失败",
                "code": "GET_WORKFLOW_ARTIFACT_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get("/{conversation_id}/{workflow_id}/artifacts/export")
def export_workflow_artifacts_endpoint(
    conversation_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """导出指定工作流当前全部真实产物，并返回 zip 压缩包"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        archive_path, archive_name = export_workflow_artifacts_archive(workflow)
        return FileResponse(
            path=archive_path,
            media_type="application/zip",
            filename=archive_name,
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
    except WorkflowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流预览不存在",
                "code": "WORKFLOW_NOT_FOUND",
                "detail": f"工作流 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except EmptyArtifactExportError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "当前工作流没有可导出的产物",
                "code": "EMPTY_WORKFLOW_ARTIFACTS",
                "detail": str(exc),
            },
        ) from exc
    except InvalidArtifactExportPathError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "工作流产物导出路径不合法",
                "code": "INVALID_WORKFLOW_EXPORT_PATH",
                "detail": str(exc),
            },
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "导出工作流产物失败",
                "code": "EXPORT_WORKFLOW_ARTIFACTS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get(
    "/{conversation_id}/{workflow_id}/runtime-logs",
    response_model=list[WorkflowRuntimeLogSchema],
)
def get_workflow_runtime_logs_endpoint(
    conversation_id: int,
    workflow_id: int,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkflowRuntimeLogSchema]:
    """返回指定工作流最近的运行日志列表，供前端日志面板回填历史"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        return list_workflow_runtime_logs(workflow, limit=limit)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except WorkflowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流预览不存在",
                "code": "WORKFLOW_NOT_FOUND",
                "detail": f"工作流 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "读取工作流运行日志失败",
                "code": "GET_WORKFLOW_RUNTIME_LOGS_FAILED",
                "detail": str(exc),
            },
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "读取工作流运行日志失败",
                "code": "GET_WORKFLOW_RUNTIME_LOGS_FAILED",
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
        workflow = create_workflow_preview(
            db,
            current_user,
            conversation,
            history_messages,
            pause_after_nodes=payload.pause_after_nodes,
        )
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
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
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

        if not workflow_concurrency_controller.reserve_slot(workflow.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "工作流并发上限已达到",
                    "code": "WORKFLOW_CONCURRENCY_LIMIT_REACHED",
                    "detail": "当前正在执行的工作流数量已达到系统上限，请稍后再试",
                },
            )

        try:
            running_workflow = mark_workflow_running(db, workflow)
            asyncio.create_task(run_workflow_execution_async(running_workflow.id))
        except Exception:
            workflow_concurrency_controller.release_slot(workflow.id)
            raise

        return workflow_to_response(running_workflow)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "对话不存在",
                "code": "CONVERSATION_NOT_FOUND",
                "detail": f"对话 `{exc}` 不存在或无权访问",
            },
        ) from exc
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


@router.post(
    "/{conversation_id}/{workflow_id}/control",
    response_model=WorkflowPreviewResponseSchema,
)
def control_workflow_endpoint(
    conversation_id: int,
    workflow_id: int,
    payload: WorkflowControlRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowPreviewResponseSchema:
    """对工作流发送暂停、恢复、中断或改向控制指令"""

    try:
        conversation = get_conversation_by_owner(db, conversation_id, current_user)
        workflow = get_workflow_by_id(db, workflow_id, conversation.id)
        workflow_run = checkpoint_controller.require_latest_run(db, workflow.id)

        if payload.action == "pause":
            checkpoint_controller.request_pause(db, workflow_run)
        elif payload.action == "resume":
            checkpoint_controller.request_resume(db, workflow_run)
        elif payload.action == "abort":
            checkpoint_controller.request_abort(db, workflow_run)
        elif payload.action == "redirect":
            if not payload.redirect_instruction.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": "改向说明不能为空",
                        "code": "MISSING_REDIRECT_INSTRUCTION",
                        "detail": "执行 redirect 时必须提供 redirect_instruction",
                    },
                )
            checkpoint_controller.request_redirect(
                db,
                workflow_run,
                payload.redirect_instruction.strip(),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "工作流控制动作不合法",
                    "code": "INVALID_WORKFLOW_CONTROL_ACTION",
                    "detail": f"当前动作 `{payload.action}` 不受支持",
                },
            )

        db.refresh(workflow)
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
    except WorkflowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流预览不存在",
                "code": "WORKFLOW_NOT_FOUND",
                "detail": f"工作流 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except WorkflowRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "工作流运行记录不存在",
                "code": "WORKFLOW_RUN_NOT_FOUND",
                "detail": f"工作流 `{exc}` 当前没有可控制的运行记录",
            },
        ) from exc
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "工作流控制失败",
                "code": "CONTROL_WORKFLOW_FAILED",
                "detail": str(exc),
            },
        ) from exc
