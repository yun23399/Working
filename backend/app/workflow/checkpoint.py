"""断点控制器，负责保存工作流快照并处理暂停、恢复、中断与改向"""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun
from app.workflow.workspace import WorkflowWorkspace


class WorkflowRunNotFoundError(Exception):
    """工作流运行记录不存在异常，供接口层转换为业务错误响应"""


class WorkflowCheckpointController:
    """工作流断点控制器，维护运行快照和外部控制指令"""

    def get_latest_run(self, db: Session, workflow_id: int) -> WorkflowRun | None:
        """读取指定工作流最近一条运行记录"""

        statement = (
            select(WorkflowRun)
            .where(WorkflowRun.workflow_id == workflow_id)
            .order_by(WorkflowRun.id.desc())
            .execution_options(populate_existing=True)
        )
        return db.scalar(statement)

    def require_latest_run(self, db: Session, workflow_id: int) -> WorkflowRun:
        """读取最近运行记录，不存在时抛出业务异常"""

        workflow_run = self.get_latest_run(db, workflow_id)
        if workflow_run is None:
            raise WorkflowRunNotFoundError(workflow_id)
        return workflow_run

    def create_run(self, db: Session, workflow: Workflow) -> WorkflowRun:
        """在工作流执行前创建新的运行记录"""

        workflow_run = WorkflowRun(
            workflow_id=workflow.id,
            status="running",
            checkpoint_json="{}",
            control_signal="none",
            redirect_instruction="",
        )
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        return workflow_run

    def finish_run(
        self,
        db: Session,
        workflow_run: WorkflowRun,
        status: str,
    ) -> WorkflowRun:
        """在工作流结束后封存当前运行记录"""

        workflow_run.status = status
        workflow_run.control_signal = "none"
        workflow_run.finished_at = datetime.now(timezone.utc)
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        return workflow_run

    def save_checkpoint(
        self,
        db: Session,
        workflow: Workflow,
        workflow_run: WorkflowRun,
        *,
        node_id: str,
        checkpoint_status: str,
        execution_logs: list[dict[str, Any]],
    ) -> WorkflowRun:
        """保存当前工作流断点快照，并同步写回运行记录"""

        workspace = WorkflowWorkspace(workflow)
        workspace_state = workspace.load_workspace_state()
        checkpoint_payload = {
            "workflow_id": workflow.id,
            "workflow_status": workflow.status,
            "workflow_progress": workflow.progress,
            "node_id": node_id,
            "checkpoint_status": checkpoint_status,
            "execution_logs": execution_logs,
            "workspace_state": workspace_state,
            "handoff_logs": workspace.load_handoffs(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        workflow_run.checkpoint_json = json.dumps(
            checkpoint_payload,
            ensure_ascii=False,
        )
        workflow_run.status = checkpoint_status
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        return workflow_run

    def request_pause(self, db: Session, workflow_run: WorkflowRun) -> WorkflowRun:
        """标记当前运行在下一个安全节点进入等待确认状态"""

        workflow_run.control_signal = "pause"
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        return workflow_run

    def request_resume(self, db: Session, workflow_run: WorkflowRun) -> WorkflowRun:
        """恢复处于等待确认状态的工作流运行"""

        workflow_run.status = "running"
        workflow_run.control_signal = "resume"
        workflow_run.redirect_instruction = ""
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        return workflow_run

    def request_abort(self, db: Session, workflow_run: WorkflowRun) -> WorkflowRun:
        """请求中断当前工作流运行"""

        workflow_run.control_signal = "abort"
        workflow_run.redirect_instruction = ""
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        return workflow_run

    def request_redirect(
        self,
        db: Session,
        workflow_run: WorkflowRun,
        instruction: str,
    ) -> WorkflowRun:
        """请求带人工改向说明的恢复执行"""

        workflow_run.status = "running"
        workflow_run.control_signal = "redirect"
        workflow_run.redirect_instruction = instruction
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        return workflow_run

    def consume_control_signal(self, db: Session, workflow_run: WorkflowRun) -> str:
        """读取并消费一次性控制信号，避免重复执行同一动作"""

        signal = workflow_run.control_signal
        if signal in {"resume", "redirect", "pause", "abort"}:
            workflow_run.control_signal = "none"
            db.add(workflow_run)
            db.commit()
            db.refresh(workflow_run)
        return signal

    def get_redirect_instruction(self, workflow_run: WorkflowRun) -> str:
        """读取当前运行挂起的改向说明"""

        return workflow_run.redirect_instruction.strip()
