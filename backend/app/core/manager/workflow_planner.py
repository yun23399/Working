"""工作流规划器，负责将结构化需求生成为最小 DAG 预览"""

from dataclasses import dataclass

from app.core.llm.adapter import LLMAdapter
from app.core.manager.requirement_extractor import RequirementSummary


@dataclass(frozen=True)
class WorkflowNode:
    """工作流节点对象，描述单个角色的任务与依赖"""

    id: str
    role: str
    task: str
    tools: list[str]
    llm: str
    max_retries: int
    depends_on: list[str]


@dataclass(frozen=True)
class WorkflowDag:
    """工作流 DAG 对象，描述最小可执行预览"""

    nodes: list[WorkflowNode]
    execution_mode: str


class WorkflowPlanner:
    """工作流规划器，根据需求摘要构造阶段二最小 DAG"""

    def __init__(self, adapter: LLMAdapter | None = None) -> None:
        """初始化规划器，用于复用当前主模型标识"""

        self.adapter = adapter or LLMAdapter()

    def plan(self, requirement: RequirementSummary) -> WorkflowDag:
        """根据结构化需求返回阶段二工作流预览 DAG"""

        runtime_label = self.adapter.get_runtime_label()
        primary_output = (
            requirement.output_types[0] if requirement.output_types else "document"
        )

        nodes = [
            WorkflowNode(
                id="node_1",
                role="需求分析师",
                task=f"梳理目标、约束与交付范围，输出执行摘要。目标：{requirement.goal}",
                tools=["file_tool"],
                llm=runtime_label,
                max_retries=2,
                depends_on=[],
            ),
            WorkflowNode(
                id="node_2",
                role="方案规划师",
                task=(
                    "根据需求摘要生成实施方案、任务拆分和风险提示，"
                    f"优先围绕 {primary_output} 类型交付。"
                ),
                tools=["file_tool"],
                llm=runtime_label,
                max_retries=2,
                depends_on=["node_1"],
            ),
            WorkflowNode(
                id="node_3",
                role="交付执行者",
                task=(
                    "根据确认后的方案产出最终交付物草稿，并整理交接说明。"
                    f"需覆盖的输出类型：{', '.join(requirement.output_types)}。"
                ),
                tools=["code_executor", "file_tool"],
                llm=runtime_label,
                max_retries=3,
                depends_on=["node_2"],
            ),
        ]

        return WorkflowDag(nodes=nodes, execution_mode="serial")
