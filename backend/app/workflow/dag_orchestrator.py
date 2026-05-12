"""DAG 编排器，负责按依赖顺序串行执行当前工作流节点"""

import asyncio
import json
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.agents.base_agent import AgentTask
from app.api.ws import connection_manager
from app.core.manager.workflow_planner import WorkflowDag, WorkflowNode
from app.models.conversation import Conversation
from app.models.workflow import Workflow
from app.services.conversation_service import save_agent_message
from app.workflow.agent_spawner import AgentSpawner
from app.workflow.checkpoint import WorkflowCheckpointController
from app.workflow.error_handler import WorkflowErrorHandler
from app.workflow.workspace import WorkflowWorkspace


class WorkflowExecutionError(Exception):
    """工作流执行异常，用于向接口层返回统一错误语义"""


class DagOrchestrator:
    """最小 DAG 编排器，当前版本只支持按依赖顺序串行执行"""

    def __init__(self, agent_spawner: AgentSpawner | None = None) -> None:
        """初始化编排器，允许注入 Agent 生成器便于扩展测试"""

        self.agent_spawner = agent_spawner or AgentSpawner()
        self.checkpoint_controller = WorkflowCheckpointController()
        self.error_handler = WorkflowErrorHandler(self.checkpoint_controller)

    def deserialize_dag(self, workflow: Workflow) -> WorkflowDag:
        """将持久化的 DAG JSON 反序列化为运行时对象"""

        payload = json.loads(workflow.dag_json)
        return WorkflowDag(
            execution_mode=payload["execution_mode"],
            nodes=[WorkflowNode(**item) for item in payload["nodes"]],
        )

    def sort_nodes(self, dag: WorkflowDag) -> list[WorkflowNode]:
        """按依赖关系解析串行执行顺序，当前阶段仅支持线性拓扑"""

        pending_nodes = {node.id: node for node in dag.nodes}
        resolved_ids: set[str] = set()
        ordered_nodes: list[WorkflowNode] = []

        while pending_nodes:
            ready_nodes = [
                node
                for node in pending_nodes.values()
                if all(dependency in resolved_ids for dependency in node.depends_on)
            ]
            if not ready_nodes:
                raise WorkflowExecutionError("当前工作流存在无法解析的循环依赖")

            ready_nodes.sort(key=lambda node: node.id)
            next_node = ready_nodes[0]
            ordered_nodes.append(next_node)
            resolved_ids.add(next_node.id)
            del pending_nodes[next_node.id]

        return ordered_nodes

    def get_latest_node_snapshot(
        self,
        db: Session,
        workflow: Workflow,
        node_id: str,
    ) -> WorkflowNode:
        """在重试或人工改向后刷新当前节点定义，避免继续使用旧配置"""

        db.refresh(workflow)
        refreshed_dag = self.deserialize_dag(workflow)
        for item in refreshed_dag.nodes:
            if item.id == node_id:
                return item
        raise WorkflowExecutionError(f"工作流节点 `{node_id}` 不存在")

    def build_node_context(
        self,
        workflow: Workflow,
        conversation: Conversation,
        execution_logs: list[dict[str, Any]],
        workspace_snapshot: str,
    ) -> str:
        """为节点执行整理最小上下文，包含需求、会话标题和前序摘要"""

        requirement_payload = json.loads(workflow.requirement_json)
        handoff_segments = [
            f"{item['role']}：{item['summary']}"
            for item in execution_logs
            if item.get("summary")
        ]
        handoff_text = (
            "\n".join(handoff_segments[-3:]) if handoff_segments else "暂无前序交接"
        )

        return (
            f"当前对话标题：{conversation.title}\n"
            f"需求目标：{requirement_payload['goal']}\n"
            f"约束：{'；'.join(requirement_payload['constraints'])}\n"
            f"最近交接：{handoff_text}\n"
            f"{workspace_snapshot}"
        )

    async def push_workflow_update(
        self,
        workflow: Workflow,
        node_id: str,
        status: str,
        progress_ratio: float,
    ) -> None:
        """向前端推送工作流节点状态更新事件"""

        await connection_manager.broadcast(
            "workflow_update",
            workflow.conversation_id,
            {
                "workflow_id": workflow.id,
                "node_id": node_id,
                "status": status,
                "progress": progress_ratio,
            },
        )

    async def push_log(
        self,
        workflow: Workflow,
        level: str,
        message: str,
        agent_id: str,
    ) -> None:
        """向前端推送工作流日志事件"""

        await connection_manager.broadcast(
            "log",
            workflow.conversation_id,
            {
                "level": level,
                "message": message,
                "agent_id": agent_id,
            },
        )

    async def execute(
        self,
        db: Session,
        workflow: Workflow,
        conversation: Conversation,
    ) -> Workflow:
        """按串行顺序执行确认后的工作流，并回写节点结果摘要"""

        dag = self.deserialize_dag(workflow)
        ordered_nodes = self.sort_nodes(dag)
        execution_logs: list[dict[str, Any]] = []
        workspace = WorkflowWorkspace(workflow)
        workspace_dir = workspace.ensure_workspace()
        self.checkpoint_controller.create_run(db, workflow)

        workflow.status = "running"
        workflow.progress = 0
        workflow.execution_log_json = json.dumps(execution_logs, ensure_ascii=False)
        workspace.save_workspace_state(
            status="running",
            progress=0,
            active_node_id=None,
            artifacts=[],
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        await self.push_log(
            workflow,
            "INFO",
            "工作流已进入执行阶段，开始按节点顺序推进",
            "orchestrator",
        )

        total_nodes = max(len(ordered_nodes), 1)
        for index, node in enumerate(ordered_nodes, start=1):
            latest_run = self.checkpoint_controller.require_latest_run(db, workflow.id)
            signal = self.checkpoint_controller.consume_control_signal(db, latest_run)
            if signal == "abort":
                workflow.status = "failed"
                workspace.save_workspace_state(
                    status="aborted",
                    progress=workflow.progress,
                    active_node_id=node.id,
                    artifacts=workspace.load_workspace_state().get("artifacts", []),
                )
                db.add(workflow)
                db.commit()
                db.refresh(workflow)
                self.checkpoint_controller.save_checkpoint(
                    db,
                    workflow,
                    latest_run,
                    node_id=node.id,
                    checkpoint_status="aborted",
                    execution_logs=execution_logs,
                )
                self.checkpoint_controller.finish_run(db, latest_run, "aborted")
                await self.push_log(
                    workflow,
                    "WARNING",
                    "工作流已收到中断指令，执行停止",
                    "orchestrator",
                )
                await self.push_workflow_update(
                    workflow,
                    node.id,
                    "aborted",
                    workflow.progress / 100,
                )
                return workflow

            progress_before = int(((index - 1) / total_nodes) * 100)
            while True:
                current_node = self.get_latest_node_snapshot(db, workflow, node.id)
                await self.push_workflow_update(
                    workflow,
                    current_node.id,
                    "running",
                    progress_before / 100,
                )
                state = workspace.load_workspace_state()
                workspace.save_workspace_state(
                    status=workflow.status,
                    progress=progress_before,
                    active_node_id=current_node.id,
                    artifacts=state.get("artifacts", []),
                    pause_after_nodes=state.get("pause_after_nodes", []),
                )
                await self.push_log(
                    workflow,
                    "INFO",
                    f"{current_node.role} 开始执行：{current_node.task}",
                    current_node.id,
                )

                try:
                    agent = self.agent_spawner.spawn(current_node)
                    task = AgentTask(
                        workflow_id=workflow.id,
                        conversation_id=workflow.conversation_id,
                        node_id=current_node.id,
                        role=current_node.role,
                        task=current_node.task,
                        context=self.build_node_context(
                            workflow,
                            conversation,
                            execution_logs,
                            workspace.get_context_snapshot(),
                        ),
                        workspace_path=str(workspace_dir),
                    )
                    result = await agent.run(task)
                    break
                except Exception as exc:
                    logger.exception(
                        "工作流 {} 节点 {} 执行失败: {}",
                        workflow.id,
                        current_node.id,
                        exc,
                    )
                    decision = self.error_handler.handle_node_error(
                        db,
                        workflow,
                        latest_run,
                        dag,
                        current_node,
                        exc,
                        execution_logs=execution_logs,
                    )
                    execution_logs = decision.execution_logs
                    await self.push_log(
                        workflow,
                        "ERROR",
                        decision.user_message,
                        current_node.id,
                    )
                    self.checkpoint_controller.save_checkpoint(
                        db,
                        workflow,
                        latest_run,
                        node_id=current_node.id,
                        checkpoint_status=decision.checkpoint_status,
                        execution_logs=execution_logs,
                        extra_payload={"error_report": decision.error_payload},
                    )
                    if decision.should_continue:
                        await self.push_log(
                            workflow,
                            "WARNING",
                            (
                                f"{current_node.role} 即将开始第 "
                                f"{decision.latest_retry_count + 1} 次尝试"
                            ),
                            "orchestrator",
                        )
                        latest_run = self.checkpoint_controller.require_latest_run(
                            db, workflow.id
                        )
                        continue

                    await self.push_workflow_update(
                        workflow,
                        current_node.id,
                        "waiting_confirm",
                        workflow.progress / 100,
                    )
                    await self.push_log(
                        workflow,
                        "WARNING",
                        decision.error_payload["recovery_suggestion"],
                        "orchestrator",
                    )
                    while True:
                        waiting_run = self.checkpoint_controller.require_latest_run(
                            db, workflow.id
                        )
                        waiting_signal = (
                            self.checkpoint_controller.consume_control_signal(
                                db, waiting_run
                            )
                        )
                        if waiting_signal == "resume":
                            workflow.status = "running"
                            restored_state = workspace.load_workspace_state()
                            workspace.save_workspace_state(
                                status="running",
                                progress=workflow.progress,
                                active_node_id=current_node.id,
                                artifacts=restored_state.get("artifacts", []),
                                pause_after_nodes=restored_state.get(
                                    "pause_after_nodes", []
                                ),
                            )
                            db.add(workflow)
                            db.commit()
                            db.refresh(workflow)
                            await self.push_log(
                                workflow,
                                "INFO",
                                (
                                    f"{current_node.role} 已收到恢复指令，"
                                    "将从失败节点重新执行"
                                ),
                                "orchestrator",
                            )
                            await self.push_workflow_update(
                                workflow,
                                current_node.id,
                                "running",
                                workflow.progress / 100,
                            )
                            latest_run = self.checkpoint_controller.require_latest_run(
                                db, workflow.id
                            )
                            break

                        if waiting_signal == "redirect":
                            redirect_instruction = (
                                self.checkpoint_controller.get_redirect_instruction(
                                    waiting_run
                                )
                            )
                            restored_state = workspace.load_workspace_state()
                            workspace.save_workspace_state(
                                status="running",
                                progress=workflow.progress,
                                active_node_id=current_node.id,
                                artifacts=restored_state.get("artifacts", []),
                                pause_after_nodes=restored_state.get(
                                    "pause_after_nodes", []
                                ),
                            )
                            handoff_logs = workspace.load_handoffs()
                            if handoff_logs:
                                handoff_logs[-1]["summary"] = (
                                    f"{handoff_logs[-1]['summary']}\n"
                                    f"人工改向说明：{redirect_instruction}"
                                )
                                workspace.restore_handoffs(handoff_logs)
                            workflow.status = "running"
                            db.add(workflow)
                            db.commit()
                            db.refresh(workflow)
                            await self.push_log(
                                workflow,
                                "INFO",
                                "失败节点已收到人工改向说明，将重新执行当前节点",
                                "orchestrator",
                            )
                            latest_run = self.checkpoint_controller.require_latest_run(
                                db, workflow.id
                            )
                            break

                        if waiting_signal == "abort":
                            workflow.status = "failed"
                            aborted_state = workspace.load_workspace_state()
                            workspace.save_workspace_state(
                                status="aborted",
                                progress=workflow.progress,
                                active_node_id=node.id,
                                artifacts=aborted_state.get("artifacts", []),
                                pause_after_nodes=aborted_state.get(
                                    "pause_after_nodes", []
                                ),
                            )
                            db.add(workflow)
                            db.commit()
                            db.refresh(workflow)
                            self.checkpoint_controller.finish_run(
                                db,
                                waiting_run,
                                "aborted",
                            )
                            await self.push_log(
                                workflow,
                                "WARNING",
                                "工作流在错误恢复等待期间被中断",
                                "orchestrator",
                            )
                            await self.push_workflow_update(
                                workflow,
                                current_node.id,
                                "aborted",
                                workflow.progress / 100,
                            )
                            return workflow

                        await asyncio.sleep(0.5)

                    latest_run = self.checkpoint_controller.require_latest_run(
                        db, workflow.id
                    )
                    continue

            execution_log = {
                "node_id": current_node.id,
                "role": current_node.role,
                "summary": result.summary,
                "status": "done",
                "artifacts": result.artifacts,
            }
            execution_logs.append(execution_log)
            workflow.execution_log_json = json.dumps(execution_logs, ensure_ascii=False)
            workflow.progress = int((index / total_nodes) * 100)
            current_state = workspace.load_workspace_state()
            artifacts = [*current_state.get("artifacts", []), *result.artifacts]
            workspace.append_handoff(
                from_agent=current_node.id,
                to_agent=ordered_nodes[index].id if index < total_nodes else "workflow",
                summary=result.summary,
                artifacts=result.artifacts,
            )
            workspace.save_workspace_state(
                status=workflow.status,
                progress=workflow.progress,
                active_node_id=None,
                artifacts=artifacts,
                pause_after_nodes=current_state.get("pause_after_nodes", []),
            )
            db.add(workflow)
            db.commit()
            db.refresh(workflow)

            save_agent_message(
                db,
                workflow.conversation_id,
                f"[{current_node.role}] {result.summary}",
                result.token_count,
            )

            await self.push_log(
                workflow,
                "INFO",
                f"{current_node.role} 已完成，结果已写入对话历史",
                current_node.id,
            )
            await self.push_workflow_update(
                workflow,
                current_node.id,
                "done",
                workflow.progress / 100,
            )

            updated_run = self.checkpoint_controller.require_latest_run(db, workflow.id)
            self.checkpoint_controller.save_checkpoint(
                db,
                workflow,
                updated_run,
                node_id=current_node.id,
                checkpoint_status="running",
                execution_logs=execution_logs,
            )

            pause_targets = workspace.load_workspace_state().get(
                "pause_after_nodes", []
            )
            if current_node.id in pause_targets:
                workflow.status = "waiting_confirm"
                workspace.save_workspace_state(
                    status="waiting_confirm",
                    progress=workflow.progress,
                    active_node_id=current_node.id,
                    artifacts=artifacts,
                    pause_after_nodes=pause_targets,
                )
                db.add(workflow)
                db.commit()
                db.refresh(workflow)
                paused_run = self.checkpoint_controller.require_latest_run(
                    db, workflow.id
                )
                self.checkpoint_controller.save_checkpoint(
                    db,
                    workflow,
                    paused_run,
                    node_id=current_node.id,
                    checkpoint_status="waiting_confirm",
                    execution_logs=execution_logs,
                )
                await self.push_log(
                    workflow,
                    "INFO",
                    (
                        f"{current_node.role} 已完成，工作流在节点 "
                        f"{current_node.id} 后进入断点等待"
                    ),
                    "orchestrator",
                )
                await self.push_workflow_update(
                    workflow,
                    current_node.id,
                    "waiting_confirm",
                    workflow.progress / 100,
                )

                while True:
                    waiting_run = self.checkpoint_controller.require_latest_run(
                        db, workflow.id
                    )
                    waiting_signal = self.checkpoint_controller.consume_control_signal(
                        db, waiting_run
                    )
                    if waiting_signal == "resume":
                        workflow.status = "running"
                        workspace.save_workspace_state(
                            status="running",
                            progress=workflow.progress,
                            active_node_id=None,
                            artifacts=artifacts,
                            pause_after_nodes=pause_targets,
                        )
                        db.add(workflow)
                        db.commit()
                        db.refresh(workflow)
                        await self.push_log(
                            workflow,
                            "INFO",
                            "工作流已收到恢复指令，继续执行后续节点",
                            "orchestrator",
                        )
                        await self.push_workflow_update(
                            workflow,
                            current_node.id,
                            "running",
                            workflow.progress / 100,
                        )
                        break

                    if waiting_signal == "redirect":
                        redirect_instruction = (
                            self.checkpoint_controller.get_redirect_instruction(
                                waiting_run
                            )
                        )
                        if redirect_instruction:
                            workspace_state = workspace.load_workspace_state()
                            workspace.save_workspace_state(
                                status="running",
                                progress=workflow.progress,
                                active_node_id=None,
                                artifacts=workspace_state.get("artifacts", []),
                                pause_after_nodes=workspace_state.get(
                                    "pause_after_nodes", []
                                ),
                            )
                            latest_handoffs = workspace.load_handoffs()
                            if latest_handoffs:
                                latest_handoffs[-1]["summary"] = (
                                    f"{latest_handoffs[-1]['summary']}\n"
                                    f"人工改向说明：{redirect_instruction}"
                                )
                                workspace.restore_handoffs(latest_handoffs)
                            workflow.status = "running"
                            db.add(workflow)
                            db.commit()
                            db.refresh(workflow)
                        await self.push_log(
                            workflow,
                            "INFO",
                            "工作流已收到改向指令，后续节点将携带人工说明继续执行",
                            "orchestrator",
                        )
                        break

                    if waiting_signal == "abort":
                        workflow.status = "failed"
                        workspace.save_workspace_state(
                            status="aborted",
                            progress=workflow.progress,
                            active_node_id=current_node.id,
                            artifacts=artifacts,
                            pause_after_nodes=pause_targets,
                        )
                        db.add(workflow)
                        db.commit()
                        db.refresh(workflow)
                        self.checkpoint_controller.finish_run(
                            db,
                            waiting_run,
                            "aborted",
                        )
                        await self.push_log(
                            workflow,
                            "WARNING",
                            "工作流在断点等待期间被中断",
                            "orchestrator",
                        )
                        await self.push_workflow_update(
                            workflow,
                            current_node.id,
                            "aborted",
                            workflow.progress / 100,
                        )
                        return workflow

                    await asyncio.sleep(0.5)

        workflow.status = "completed"
        workflow.progress = 100
        final_state = workspace.load_workspace_state()
        workspace.save_workspace_state(
            status="completed",
            progress=100,
            active_node_id=None,
            artifacts=final_state.get("artifacts", []),
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        await self.push_log(
            workflow,
            "INFO",
            "工作流执行完成",
            "orchestrator",
        )
        await self.push_workflow_update(
            workflow,
            "workflow",
            "done",
            1.0,
        )
        final_run = self.checkpoint_controller.require_latest_run(db, workflow.id)
        self.checkpoint_controller.finish_run(db, final_run, "completed")
        return workflow
