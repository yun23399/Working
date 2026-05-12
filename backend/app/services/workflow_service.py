"""工作流服务层，负责预览生成、持久化与确认更新"""

import json
from dataclasses import asdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, object_session

from app.core.manager.manager_agent import ManagerConversationMessage
from app.core.manager.requirement_extractor import RequirementExtractor
from app.core.manager.workflow_planner import WorkflowPlanner
from app.models.conversation import Conversation
from app.models.workflow import Workflow
from app.schemas.workflow import (
    RequirementSummarySchema,
    WorkflowDagSchema,
    WorkflowExecutionLogSchema,
    WorkflowHandoffSchema,
    WorkflowNodeSchema,
    WorkflowPreviewResponseSchema,
    WorkflowRunSchema,
    WorkflowWorkspaceStateSchema,
)
from app.workflow.checkpoint import WorkflowCheckpointController
from app.workflow.workspace import WorkflowWorkspace


class WorkflowNotFoundError(Exception):
    """工作流不存在异常，供路由层转换为业务错误响应"""


def list_workflows_by_conversation(
    db: Session,
    conversation_id: int,
) -> list[Workflow]:
    """返回指定对话下的工作流记录，按创建时间倒序排序"""

    statement = (
        select(Workflow)
        .where(Workflow.conversation_id == conversation_id)
        .order_by(Workflow.created_at.desc(), Workflow.id.desc())
    )
    return list(db.scalars(statement).all())


def get_workflow_by_id(
    db: Session,
    workflow_id: int,
    conversation_id: int,
) -> Workflow:
    """根据编号读取指定对话下的工作流记录"""

    statement = select(Workflow).where(
        Workflow.id == workflow_id,
        Workflow.conversation_id == conversation_id,
    )
    workflow = db.scalar(statement)
    if workflow is None:
        raise WorkflowNotFoundError(workflow_id)
    return workflow


def create_workflow_preview(
    db: Session,
    conversation: Conversation,
    history_messages: list[ManagerConversationMessage],
    pause_after_nodes: list[str] | None = None,
) -> Workflow:
    """根据当前对话历史生成工作流预览并持久化"""

    requirement = RequirementExtractor().extract(conversation.title, history_messages)
    dag = WorkflowPlanner().plan(requirement)

    workflow = Workflow(
        conversation_id=conversation.id,
        requirement_json=json.dumps(asdict(requirement), ensure_ascii=False),
        dag_json=json.dumps(asdict(dag), ensure_ascii=False),
        execution_log_json="[]",
        workspace_state_json="{}",
        handoff_log_json="[]",
        workspace_path="",
        progress=0,
        status="draft",
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    workspace = WorkflowWorkspace(workflow)
    workspace_dir = workspace.ensure_workspace()
    workspace.save_workspace_state(
        status=workflow.status,
        progress=workflow.progress,
        active_node_id=None,
        artifacts=[],
        pause_after_nodes=pause_after_nodes or [],
    )
    workflow.workspace_path = str(workspace_dir)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def confirm_workflow_preview(db: Session, workflow: Workflow) -> Workflow:
    """将工作流预览标记为已确认，供后续阶段执行使用"""

    workflow.status = "confirmed"
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def mark_workflow_running(db: Session, workflow: Workflow) -> Workflow:
    """将工作流标记为运行中，并清空上一轮执行现场"""

    workflow.status = "running"
    workflow.progress = 0
    workflow.execution_log_json = "[]"
    workflow.handoff_log_json = "[]"
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    workspace = WorkflowWorkspace(workflow)
    workspace.ensure_workspace()
    workspace.save_workspace_state(
        status=workflow.status,
        progress=workflow.progress,
        active_node_id=None,
        artifacts=[],
        pause_after_nodes=workspace.load_workspace_state().get("pause_after_nodes", []),
    )
    workflow.workspace_path = str(workspace.resolve_workspace_path())
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def build_node_runtime_status_map(
    workflow: Workflow,
    dag_payload: dict[str, Any],
    execution_log_payload: list[dict[str, Any]],
) -> dict[str, str]:
    """根据当前工作流状态和执行日志推导节点运行态"""

    node_ids = [str(node["id"]) for node in dag_payload["nodes"]]
    completed_node_ids = {
        str(item["node_id"])
        for item in execution_log_payload
        if item.get("status") == "done" and item.get("node_id") is not None
    }
    first_pending_node_id = next(
        (node_id for node_id in node_ids if node_id not in completed_node_ids),
        None,
    )

    runtime_status_map: dict[str, str] = {}
    for node_id in node_ids:
        if workflow.status == "completed":
            runtime_status_map[node_id] = "done"
            continue

        if node_id in completed_node_ids:
            runtime_status_map[node_id] = "done"
            continue

        if workflow.status == "running" and node_id == first_pending_node_id:
            runtime_status_map[node_id] = "running"
            continue

        if workflow.status == "failed" and node_id == first_pending_node_id:
            runtime_status_map[node_id] = "failed"
            continue

        runtime_status_map[node_id] = "waiting"

    return runtime_status_map


def workflow_to_response(workflow: Workflow) -> WorkflowPreviewResponseSchema:
    """将工作流模型转换为前端消费的预览响应结构"""

    requirement_payload = json.loads(workflow.requirement_json)
    dag_payload = json.loads(workflow.dag_json)
    execution_log_payload = json.loads(workflow.execution_log_json or "[]")
    handoff_log_payload = json.loads(workflow.handoff_log_json or "[]")
    runtime_status_map = build_node_runtime_status_map(
        workflow,
        dag_payload,
        execution_log_payload,
    )
    workspace_manager = WorkflowWorkspace(workflow)
    checkpoint_controller = WorkflowCheckpointController()
    workspace_state_payload = (
        json.loads(workflow.workspace_state_json)
        if workflow.workspace_state_json and workflow.workspace_state_json != "{}"
        else workspace_manager.build_default_state()
    )
    workspace_path = workflow.workspace_path or str(
        workspace_manager.resolve_workspace_path()
    )
    db_session = object_session(workflow)
    latest_run = (
        checkpoint_controller.get_latest_run(db=db_session, workflow_id=workflow.id)
        if db_session is not None
        else None
    )
    checkpoint_payload = (
        json.loads(latest_run.checkpoint_json)
        if (
            latest_run
            and latest_run.checkpoint_json
            and latest_run.checkpoint_json != "{}"
        )
        else {}
    )

    return WorkflowPreviewResponseSchema(
        workflow_id=workflow.id,
        conversation_id=workflow.conversation_id,
        status=workflow.status,
        progress=workflow.progress,
        requirement=RequirementSummarySchema(**requirement_payload),
        dag=WorkflowDagSchema(
            execution_mode=dag_payload["execution_mode"],
            nodes=[
                WorkflowNodeSchema(
                    **node,
                    runtime_status=runtime_status_map.get(str(node["id"])),
                )
                for node in dag_payload["nodes"]
            ],
        ),
        execution_logs=[
            WorkflowExecutionLogSchema(**item) for item in execution_log_payload
        ],
        workspace=WorkflowWorkspaceStateSchema(
            workspace_path=workspace_path,
            status=workspace_state_payload.get("status", workflow.status),
            progress=workspace_state_payload.get("progress", workflow.progress),
            active_node_id=workspace_state_payload.get("active_node_id"),
            artifacts=workspace_state_payload.get("artifacts", []),
            updated_at=workspace_state_payload.get("updated_at", ""),
            pause_after_nodes=workspace_state_payload.get("pause_after_nodes", []),
        ),
        handoff_logs=[WorkflowHandoffSchema(**item) for item in handoff_log_payload],
        workflow_run=WorkflowRunSchema(
            run_id=latest_run.id if latest_run else None,
            status=latest_run.status if latest_run else "idle",
            control_signal=latest_run.control_signal if latest_run else "none",
            checkpoint_node_id=checkpoint_payload.get("node_id"),
            redirect_instruction=latest_run.redirect_instruction if latest_run else "",
            saved_at=checkpoint_payload.get("saved_at"),
        ),
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )
