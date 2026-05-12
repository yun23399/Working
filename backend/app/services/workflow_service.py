"""工作流服务层，负责预览生成、持久化与确认更新"""

import json
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.manager.manager_agent import ManagerConversationMessage
from app.core.manager.requirement_extractor import RequirementExtractor
from app.core.manager.workflow_planner import WorkflowPlanner
from app.models.conversation import Conversation
from app.models.workflow import Workflow
from app.schemas.workflow import (
    RequirementSummarySchema,
    WorkflowDagSchema,
    WorkflowNodeSchema,
    WorkflowPreviewResponseSchema,
)


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
) -> Workflow:
    """根据当前对话历史生成工作流预览并持久化"""

    requirement = RequirementExtractor().extract(conversation.title, history_messages)
    dag = WorkflowPlanner().plan(requirement)

    workflow = Workflow(
        conversation_id=conversation.id,
        requirement_json=json.dumps(asdict(requirement), ensure_ascii=False),
        dag_json=json.dumps(asdict(dag), ensure_ascii=False),
        status="draft",
    )
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


def workflow_to_response(workflow: Workflow) -> WorkflowPreviewResponseSchema:
    """将工作流模型转换为前端消费的预览响应结构"""

    requirement_payload = json.loads(workflow.requirement_json)
    dag_payload = json.loads(workflow.dag_json)

    return WorkflowPreviewResponseSchema(
        workflow_id=workflow.id,
        conversation_id=workflow.conversation_id,
        status=workflow.status,
        requirement=RequirementSummarySchema(**requirement_payload),
        dag=WorkflowDagSchema(
            execution_mode=dag_payload["execution_mode"],
            nodes=[WorkflowNodeSchema(**node) for node in dag_payload["nodes"]],
        ),
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )
