"""工作流错误处理器，负责节点失败后的重试、回滚与层级上报"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.core.manager.workflow_planner import WorkflowDag, WorkflowNode
from app.core.memory.project_memory import ProjectMemoryManager
from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun
from app.workflow.checkpoint import WorkflowCheckpointController
from app.workflow.workspace import WorkflowWorkspace


@dataclass(frozen=True)
class WorkflowRecoveryDecision:
    """错误处理决策对象，统一返回恢复后的运行态信息"""

    should_continue: bool
    next_status: str
    progress: int
    execution_logs: list[dict[str, Any]]
    workspace_state: dict[str, Any]
    handoff_logs: list[dict[str, Any]]
    error_payload: dict[str, Any]
    user_message: str
    checkpoint_status: str
    latest_retry_count: int


class WorkflowErrorHandler:
    """工作流错误处理器，封装失败节点的恢复与上报策略"""

    def __init__(
        self,
        checkpoint_controller: WorkflowCheckpointController | None = None,
    ) -> None:
        """初始化错误处理器，允许复用同一套断点控制能力"""

        self.checkpoint_controller = (
            checkpoint_controller or WorkflowCheckpointController()
        )

    def handle_node_error(
        self,
        db: Session,
        workflow: Workflow,
        workflow_run: WorkflowRun,
        dag: WorkflowDag,
        failed_node: WorkflowNode,
        exc: Exception,
        execution_logs: list[dict[str, Any]],
    ) -> WorkflowRecoveryDecision:
        """处理节点失败，返回重试或人工介入所需的恢复决策"""

        checkpoint_payload = self.checkpoint_controller.load_checkpoint_payload(
            workflow_run
        )
        retry_count = self._resolve_retry_count(workflow_run, failed_node.id) + 1
        can_retry = retry_count <= failed_node.max_retries
        workspace = WorkflowWorkspace(workflow)
        project_memory = ProjectMemoryManager(workflow)

        rollback_state = self._build_rollback_state(
            workflow=workflow,
            failed_node=failed_node,
            checkpoint_payload=checkpoint_payload,
        )
        rollback_handoffs = self._build_rollback_handoffs(checkpoint_payload)
        rollback_logs = self._build_rollback_logs(checkpoint_payload, execution_logs)
        report_line = self._build_report_line(dag, failed_node, exc, retry_count)
        error_payload = self._build_error_payload(
            dag=dag,
            failed_node=failed_node,
            exc=exc,
            retry_count=retry_count,
            can_retry=can_retry,
            checkpoint_payload=checkpoint_payload,
            rollback_state=rollback_state,
        )
        recovery_suggestion = self._build_recovery_suggestion(
            dag=dag,
            failed_node=failed_node,
            exc=exc,
            checkpoint_payload=checkpoint_payload,
        )
        project_memory.record_error(
            node_id=failed_node.id,
            role=failed_node.role,
            error_message=str(exc),
            recovery_suggestion=recovery_suggestion,
        )

        logger.error(
            "工作流 {} 节点 {} 失败，重试 {}/{}，建议动作：{}",
            workflow.id,
            failed_node.id,
            retry_count,
            failed_node.max_retries,
            "retry" if can_retry else "waiting_confirm",
        )

        if can_retry:
            workflow.status = "running"
            workflow.progress = rollback_state.get("progress", workflow.progress)
            workflow.execution_log_json = self._dumps_json(rollback_logs)
            workspace.restore_workspace_state(
                {
                    **rollback_state,
                    "status": "running",
                    "active_node_id": failed_node.id,
                }
            )
            workspace.restore_handoffs(rollback_handoffs)
            db.add(workflow)
            db.commit()
            db.refresh(workflow)
            return WorkflowRecoveryDecision(
                should_continue=True,
                next_status="running",
                progress=workflow.progress,
                execution_logs=rollback_logs,
                workspace_state=workspace.load_workspace_state(),
                handoff_logs=rollback_handoffs,
                error_payload=error_payload,
                user_message=(f"{report_line}，系统将按重试策略自动重新执行当前节点。"),
                checkpoint_status="retrying",
                latest_retry_count=retry_count,
            )

        workflow.status = "waiting_confirm"
        workflow.progress = rollback_state.get("progress", workflow.progress)
        workflow.execution_log_json = self._dumps_json(rollback_logs)
        workspace.restore_workspace_state(
            {
                **rollback_state,
                "status": "waiting_confirm",
                "active_node_id": failed_node.id,
            }
        )
        workspace.restore_handoffs(rollback_handoffs)
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        error_payload["recovery_suggestion"] = recovery_suggestion
        return WorkflowRecoveryDecision(
            should_continue=False,
            next_status="waiting_confirm",
            progress=workflow.progress,
            execution_logs=rollback_logs,
            workspace_state=workspace.load_workspace_state(),
            handoff_logs=rollback_handoffs,
            error_payload=error_payload,
            user_message=f"{report_line}，已回滚到最近安全快照，等待人工恢复。",
            checkpoint_status="waiting_confirm",
            latest_retry_count=retry_count,
        )

    def _resolve_retry_count(self, workflow_run: WorkflowRun, node_id: str) -> int:
        """从最近一次快照中读取当前节点已消耗的重试次数"""

        payload = self.checkpoint_controller.load_checkpoint_payload(workflow_run)
        error_report = payload.get("error_report")
        if (
            isinstance(error_report, dict)
            and error_report.get("failed_node_id") == node_id
            and isinstance(error_report.get("retry_count"), int)
        ):
            return int(error_report["retry_count"])
        return 0

    def _build_rollback_state(
        self,
        *,
        workflow: Workflow,
        failed_node: WorkflowNode,
        checkpoint_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """根据最近快照构造失败后的回滚工作区状态"""

        workspace = WorkflowWorkspace(workflow)
        default_state = workspace.build_default_state()
        checkpoint_state = checkpoint_payload.get("workspace_state")
        if not isinstance(checkpoint_state, dict):
            checkpoint_state = default_state

        return {
            "workflow_id": workflow.id,
            "conversation_id": workflow.conversation_id,
            "status": checkpoint_state.get("status", workflow.status),
            "progress": int(checkpoint_state.get("progress", workflow.progress)),
            "active_node_id": failed_node.id,
            "artifacts": checkpoint_state.get("artifacts", []),
            "pause_after_nodes": checkpoint_state.get("pause_after_nodes", []),
            "updated_at": workspace.build_timestamp(),
        }

    def _build_rollback_handoffs(
        self,
        checkpoint_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """从快照中恢复最近安全交接记录"""

        handoff_logs = checkpoint_payload.get("handoff_logs", [])
        return handoff_logs if isinstance(handoff_logs, list) else []

    def _build_rollback_logs(
        self,
        checkpoint_payload: dict[str, Any],
        execution_logs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """以最近快照为准恢复已成功节点的执行日志"""

        checkpoint_logs = checkpoint_payload.get("execution_logs", [])
        if isinstance(checkpoint_logs, list):
            return checkpoint_logs
        return execution_logs

    def _build_report_line(
        self,
        dag: WorkflowDag,
        failed_node: WorkflowNode,
        exc: Exception,
        retry_count: int,
    ) -> str:
        """生成简短的人类可读失败上报文本"""

        upstream_node = self._find_upstream_node(dag, failed_node)
        upstream_role = upstream_node.role if upstream_node else "Manager"
        return (
            f"{failed_node.role} 节点执行失败，已向上级 {upstream_role} 上报。"
            f"失败原因：{exc}。当前累计重试 {retry_count} 次"
        )

    def _build_recovery_suggestion(
        self,
        *,
        dag: WorkflowDag,
        failed_node: WorkflowNode,
        exc: Exception,
        checkpoint_payload: dict[str, Any],
    ) -> str:
        """基于失败节点和上游上下文生成恢复建议"""

        upstream_node = self._find_upstream_node(dag, failed_node)
        upstream_role = upstream_node.role if upstream_node else "Manager"
        checkpoint_node_id = checkpoint_payload.get("node_id") or "最近安全节点"
        return (
            f"建议先检查 {failed_node.role} 节点任务描述是否过宽或上下文不足；"
            f"若需继续，可通过 redirect 向 {upstream_role} 补充更明确的交付边界，"
            f"并从 {checkpoint_node_id} 对应快照恢复后重试。"
            f"本次错误：{exc}"
        )

    def _build_error_payload(
        self,
        *,
        dag: WorkflowDag,
        failed_node: WorkflowNode,
        exc: Exception,
        retry_count: int,
        can_retry: bool,
        checkpoint_payload: dict[str, Any],
        rollback_state: dict[str, Any],
    ) -> dict[str, Any]:
        """构造持久化的错误报告，供前端和控制接口消费"""

        upstream_node = self._find_upstream_node(dag, failed_node)
        return {
            "failed_node_id": failed_node.id,
            "failed_role": failed_node.role,
            "task": failed_node.task,
            "error_message": str(exc),
            "retry_count": retry_count,
            "max_retries": failed_node.max_retries,
            "can_retry": can_retry,
            "upstream_node_id": upstream_node.id if upstream_node else None,
            "upstream_role": upstream_node.role if upstream_node else "Manager",
            "rollback_checkpoint_node_id": checkpoint_payload.get("node_id"),
            "rollback_progress": rollback_state.get("progress", 0),
        }

    def _find_upstream_node(
        self,
        dag: WorkflowDag,
        failed_node: WorkflowNode,
    ) -> WorkflowNode | None:
        """根据 DAG 依赖关系定位失败节点的直接上游节点"""

        if not failed_node.depends_on:
            return None

        dependency_map = {node.id: node for node in dag.nodes}
        for dependency_id in reversed(failed_node.depends_on):
            if dependency_id in dependency_map:
                return dependency_map[dependency_id]
        return None

    @staticmethod
    def _dumps_json(payload: list[dict[str, Any]]) -> str:
        """统一处理 JSON 序列化，避免重复书写参数"""

        import json

        return json.dumps(payload, ensure_ascii=False)
