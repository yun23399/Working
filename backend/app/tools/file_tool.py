"""文件读写工具，负责在共享工作区内安全读写文本文件"""

from __future__ import annotations

import json
from pathlib import Path

from app.tools.base_tool import BaseTool, ToolExecutionResult


class FileToolError(Exception):
    """文件工具异常，供上层统一捕获与处理"""


class FileTool(BaseTool):
    """文件读写工具，仅允许在共享工作区内读写文本文件"""

    def __init__(self) -> None:
        """初始化文件工具名称"""

        super().__init__(tool_name="file_tool")

    async def execute(
        self,
        *,
        workspace_path: str,
        instruction: str,
    ) -> ToolExecutionResult:
        """解析读写指令，并在工作区内执行安全文件操作"""

        try:
            payload = json.loads(instruction)
        except json.JSONDecodeError as exc:
            raise FileToolError("文件工具指令必须是合法 JSON") from exc

        action = str(payload.get("action", "")).strip().lower()
        relative_path = str(payload.get("path", "")).strip()
        workspace_dir = Path(workspace_path).resolve()

        if not action:
            raise FileToolError("文件工具缺少 action 参数")
        if not relative_path:
            raise FileToolError("文件工具缺少 path 参数")

        target_path = self.resolve_target_path(
            workspace_dir=workspace_dir,
            relative_path=relative_path,
        )

        if action == "write":
            content = str(payload.get("content", ""))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            return ToolExecutionResult(
                summary=(
                    f"已写入文件：{target_path.name}；"
                    f"相对路径：{relative_path}；内容长度：{len(content)} 字符。"
                ),
                artifacts=[str(target_path)],
                raw_output=content,
                exit_code=0,
            )

        if action == "read":
            if not target_path.exists():
                raise FileToolError(f"目标文件不存在：{relative_path}")
            content = target_path.read_text(encoding="utf-8")
            return ToolExecutionResult(
                summary=(
                    f"已读取文件：{target_path.name}；"
                    f"相对路径：{relative_path}；内容长度：{len(content)} 字符。"
                ),
                artifacts=[],
                raw_output=content,
                exit_code=0,
            )

        raise FileToolError(f"不支持的文件操作：{action}")

    def resolve_target_path(
        self,
        *,
        workspace_dir: Path,
        relative_path: str,
    ) -> Path:
        """解析目标路径，并阻止跳出共享工作区目录"""

        candidate_path = (workspace_dir / relative_path).resolve()
        if not candidate_path.is_relative_to(workspace_dir):
            raise FileToolError("文件路径越界，禁止访问工作区之外的路径")
        return candidate_path
