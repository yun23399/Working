"""共享工作区管理器，负责为工作流维护统一的运行时目录与状态快照"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import settings
from app.models.workflow import Workflow


@dataclass(frozen=True)
class WorkspaceHandoff:
    """共享工作区中的交接记录，描述节点之间的最小交付信息"""

    from_agent: str
    to_agent: str
    summary: str
    artifacts: list[str]
    created_at: str


class WorkflowWorkspace:
    """共享工作区实体，提供目录初始化、状态回写和交接记录能力"""

    def __init__(self, workflow: Workflow) -> None:
        """基于当前工作流初始化共享工作区对象"""

        self.workflow = workflow

    def resolve_workspace_path(self) -> Path:
        """解析当前工作流的专属工作区目录，首次使用时按约定生成"""

        if self.workflow.workspace_path:
            return Path(self.workflow.workspace_path).resolve()

        root_dir = settings.workspace_dir_path
        return (
            root_dir
            / "projects"
            / f"conversation_{self.workflow.conversation_id}"
            / f"workflow_{self.workflow.id}"
        )

    def ensure_workspace(self) -> Path:
        """确保共享工作区目录和基础文件结构存在"""

        workspace_dir = self.resolve_workspace_path()
        artifacts_dir = workspace_dir / "artifacts"
        context_dir = workspace_dir / "context"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        context_dir.mkdir(parents=True, exist_ok=True)

        state_path = context_dir / "workspace_state.json"
        if not state_path.exists():
            state_path.write_text(
                json.dumps(self.build_default_state(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        handoff_path = context_dir / "handoff_log.json"
        if not handoff_path.exists():
            handoff_path.write_text("[]", encoding="utf-8")

        logger.debug("工作流 {} 共享工作区已就绪: {}", self.workflow.id, workspace_dir)
        return workspace_dir

    def build_default_state(self) -> dict[str, Any]:
        """构造共享工作区的默认状态快照"""

        return {
            "workflow_id": self.workflow.id,
            "conversation_id": self.workflow.conversation_id,
            "status": self.workflow.status,
            "progress": self.workflow.progress,
            "active_node_id": None,
            "artifacts": [],
            "updated_at": self.build_timestamp(),
        }

    def load_workspace_state(self) -> dict[str, Any]:
        """读取工作区状态快照，若文件缺失则返回默认结构"""

        workspace_dir = self.ensure_workspace()
        state_path = workspace_dir / "context" / "workspace_state.json"
        if not state_path.exists():
            return self.build_default_state()

        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning(
                "工作流 {} 的工作区状态文件损坏，已回退默认状态",
                self.workflow.id,
            )
            return self.build_default_state()

    def save_workspace_state(
        self,
        *,
        status: str,
        progress: int,
        active_node_id: str | None,
        artifacts: list[str],
    ) -> dict[str, Any]:
        """持久化最新工作区状态，并同步回模型字段"""

        workspace_dir = self.ensure_workspace()
        state = {
            "workflow_id": self.workflow.id,
            "conversation_id": self.workflow.conversation_id,
            "status": status,
            "progress": progress,
            "active_node_id": active_node_id,
            "artifacts": artifacts,
            "updated_at": self.build_timestamp(),
        }
        state_path = workspace_dir / "context" / "workspace_state.json"
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.workflow.workspace_path = str(workspace_dir)
        self.workflow.workspace_state_json = json.dumps(state, ensure_ascii=False)
        return state

    def load_handoffs(self) -> list[dict[str, Any]]:
        """读取当前工作流已有的交接记录"""

        workspace_dir = self.ensure_workspace()
        handoff_path = workspace_dir / "context" / "handoff_log.json"
        if not handoff_path.exists():
            return []

        try:
            return json.loads(handoff_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("工作流 {} 的交接日志损坏，已忽略旧数据", self.workflow.id)
            return []

    def append_handoff(
        self,
        *,
        from_agent: str,
        to_agent: str,
        summary: str,
        artifacts: list[str],
    ) -> list[dict[str, Any]]:
        """追加一条节点交接记录，并同步写回数据库字段"""

        workspace_dir = self.ensure_workspace()
        handoff_path = workspace_dir / "context" / "handoff_log.json"
        handoffs = self.load_handoffs()
        handoff = WorkspaceHandoff(
            from_agent=from_agent,
            to_agent=to_agent,
            summary=summary,
            artifacts=artifacts,
            created_at=self.build_timestamp(),
        )
        handoffs.append(handoff.__dict__)
        handoff_path.write_text(
            json.dumps(handoffs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.workflow.workspace_path = str(workspace_dir)
        self.workflow.handoff_log_json = json.dumps(handoffs, ensure_ascii=False)
        return handoffs

    def get_context_snapshot(self) -> str:
        """将共享工作区状态与最近交接整理为文本，供执行 Agent 使用"""

        state = self.load_workspace_state()
        handoffs = self.load_handoffs()
        if handoffs:
            recent_handoffs = "\n".join(
                f"{item['from_agent']} -> {item['to_agent']}：{item['summary']}"
                for item in handoffs[-3:]
            )
        else:
            recent_handoffs = "暂无交接记录"

        artifacts = state.get("artifacts", [])
        artifact_text = "、".join(artifacts[-5:]) if artifacts else "暂无产出物"
        status = state.get("status", "unknown")
        progress = state.get("progress", 0)
        return (
            f"工作区状态：{status}，进度 {progress}%\n"
            f"当前活跃节点：{state.get('active_node_id') or '无'}\n"
            f"最近交接：{recent_handoffs}\n"
            f"当前产出物：{artifact_text}"
        )

    @staticmethod
    def build_timestamp() -> str:
        """生成统一的 UTC 时间戳字符串"""

        return datetime.now(timezone.utc).isoformat()
