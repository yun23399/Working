"""项目级记忆管理器，负责维护对话级共享长期上下文"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.workflow import Workflow
from app.workflow.workspace import WorkflowWorkspace

MAX_KEY_POINT_COUNT = 8
MAX_ARTIFACT_COUNT = 10
MAX_HISTORY_COUNT = 10


class ProjectMemoryManager:
    """项目级记忆管理器，为同一对话下的工作流维护共享记忆"""

    def __init__(self, workflow: Workflow) -> None:
        """基于当前工作流初始化项目级记忆管理器"""

        self.workflow = workflow
        self.workspace = WorkflowWorkspace(workflow)

    def resolve_memory_path(self) -> Path:
        """定位当前对话对应的项目级记忆文件路径"""

        workflow_dir = self.workspace.resolve_workspace_path()
        conversation_dir = workflow_dir.parent
        return conversation_dir / "project_memory.json"

    def build_default_memory(self) -> dict[str, Any]:
        """构造项目级记忆的默认结构"""

        return {
            "conversation_id": self.workflow.conversation_id,
            "latest_goal": "",
            "active_constraints": [],
            "key_points": [],
            "artifacts": [],
            "workflow_history": [],
            "latest_error": None,
            "updated_at": self.workspace.build_timestamp(),
        }

    def ensure_memory(self) -> Path:
        """确保项目级记忆文件存在"""

        memory_path = self.resolve_memory_path()
        memory_path.parent.mkdir(parents=True, exist_ok=True)
        if not memory_path.exists():
            memory_path.write_text(
                json.dumps(self.build_default_memory(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return memory_path

    def load_memory(self) -> dict[str, Any]:
        """读取当前项目级记忆，损坏时退回默认结构"""

        memory_path = self.ensure_memory()
        try:
            return json.loads(memory_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return self.build_default_memory()

    def save_memory(self, payload: dict[str, Any]) -> dict[str, Any]:
        """持久化项目级记忆，并统一刷新更新时间"""

        memory_path = self.ensure_memory()
        payload["conversation_id"] = self.workflow.conversation_id
        payload["updated_at"] = self.workspace.build_timestamp()
        memory_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return payload

    def register_requirement(
        self,
        goal: str,
        constraints: list[str],
    ) -> dict[str, Any]:
        """在生成工作流预览时写入最新需求摘要"""

        memory = self.load_memory()
        memory["latest_goal"] = goal
        memory["active_constraints"] = constraints[:MAX_KEY_POINT_COUNT]
        memory["key_points"] = self.merge_unique_items(
            memory.get("key_points", []),
            [goal, *constraints],
            MAX_KEY_POINT_COUNT,
        )
        memory["workflow_history"] = self.upsert_workflow_history(
            memory.get("workflow_history", []),
            workflow_id=self.workflow.id,
            status=self.workflow.status,
            summary=goal,
        )
        return self.save_memory(memory)

    def record_node_result(
        self,
        *,
        node_id: str,
        role: str,
        summary: str,
        artifacts: list[str],
    ) -> dict[str, Any]:
        """记录节点完成摘要，沉淀到项目级记忆"""

        memory = self.load_memory()
        memory["key_points"] = self.merge_unique_items(
            memory.get("key_points", []),
            [f"{role}({node_id})：{summary}"],
            MAX_KEY_POINT_COUNT,
        )
        memory["artifacts"] = self.merge_unique_items(
            memory.get("artifacts", []),
            artifacts,
            MAX_ARTIFACT_COUNT,
        )
        memory["workflow_history"] = self.upsert_workflow_history(
            memory.get("workflow_history", []),
            workflow_id=self.workflow.id,
            status=self.workflow.status,
            summary=summary,
        )

        latest_error = memory.get("latest_error")
        if (
            isinstance(latest_error, dict)
            and latest_error.get("workflow_id") == self.workflow.id
        ):
            memory["latest_error"] = None

        return self.save_memory(memory)

    def record_error(
        self,
        *,
        node_id: str,
        role: str,
        error_message: str,
        recovery_suggestion: str,
    ) -> dict[str, Any]:
        """记录最近一次失败节点信息，供人工恢复时参考"""

        memory = self.load_memory()
        memory["latest_error"] = {
            "workflow_id": self.workflow.id,
            "node_id": node_id,
            "role": role,
            "error_message": error_message,
            "recovery_suggestion": recovery_suggestion,
            "updated_at": self.workspace.build_timestamp(),
        }
        memory["workflow_history"] = self.upsert_workflow_history(
            memory.get("workflow_history", []),
            workflow_id=self.workflow.id,
            status=self.workflow.status,
            summary=f"{role} 节点失败：{error_message}",
        )
        return self.save_memory(memory)

    def build_response_payload(self) -> dict[str, Any]:
        """将项目级记忆转换为前端可消费的响应结构"""

        memory = self.load_memory()
        return {
            "memory_path": str(self.resolve_memory_path()),
            "latest_goal": memory.get("latest_goal", ""),
            "active_constraints": memory.get("active_constraints", []),
            "key_points": memory.get("key_points", []),
            "artifacts": memory.get("artifacts", []),
            "workflow_count": len(memory.get("workflow_history", [])),
            "latest_error": memory.get("latest_error"),
            "updated_at": memory.get("updated_at", ""),
        }

    def get_context_snapshot(self) -> str:
        """生成项目级记忆文本快照，供节点执行时拼接上下文"""

        payload = self.build_response_payload()
        latest_goal = payload["latest_goal"] or "暂无长期目标"
        key_points = payload["key_points"]
        key_points_text = "；".join(key_points[-4:]) if key_points else "暂无关键记忆"
        artifacts = payload["artifacts"]
        artifact_text = "、".join(artifacts[-5:]) if artifacts else "暂无产出物"
        latest_error = payload["latest_error"]
        latest_error_text = (
            f"{latest_error['role']}({latest_error['node_id']})："
            f"{latest_error['error_message']}"
            if isinstance(latest_error, dict)
            else "无"
        )
        return (
            f"项目长期目标：{latest_goal}\n"
            f"项目关键记忆：{key_points_text}\n"
            f"项目累计产出：{artifact_text}\n"
            f"最近异常：{latest_error_text}"
        )

    def upsert_workflow_history(
        self,
        workflow_history: list[dict[str, Any]],
        *,
        workflow_id: int,
        status: str,
        summary: str,
    ) -> list[dict[str, Any]]:
        """更新当前工作流在项目级记忆中的历史摘要"""

        current_history = [
            item for item in workflow_history if item.get("workflow_id") != workflow_id
        ]
        current_history.insert(
            0,
            {
                "workflow_id": workflow_id,
                "status": status,
                "summary": summary[:200],
                "updated_at": self.workspace.build_timestamp(),
            },
        )
        return current_history[:MAX_HISTORY_COUNT]

    @staticmethod
    def merge_unique_items(
        existing_items: list[str],
        incoming_items: list[str],
        limit: int,
    ) -> list[str]:
        """合并并去重字符串列表，保留最近有效内容"""

        merged_items = [
            item for item in existing_items if isinstance(item, str) and item
        ]
        for item in incoming_items:
            if not isinstance(item, str):
                continue
            normalized_item = item.strip()
            if not normalized_item:
                continue
            if normalized_item in merged_items:
                merged_items.remove(normalized_item)
            merged_items.append(normalized_item)
        return merged_items[-limit:]
