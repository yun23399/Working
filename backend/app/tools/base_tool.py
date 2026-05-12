"""工具基类定义，统一约束工作流工具的输入输出结构"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolExecutionResult:
    """工具执行结果对象，包含摘要、产出物和原始输出"""

    summary: str
    artifacts: list[str]
    raw_output: str
    exit_code: int


class BaseTool:
    """工具基类，约束所有工具的最小执行接口"""

    tool_name: str

    def __init__(self, tool_name: str) -> None:
        """初始化工具名称，便于运行期日志与调度识别"""

        self.tool_name = tool_name

    async def execute(
        self,
        *,
        workspace_path: str,
        instruction: str,
    ) -> ToolExecutionResult:
        """执行具体工具逻辑，子类必须实现"""

        raise NotImplementedError
