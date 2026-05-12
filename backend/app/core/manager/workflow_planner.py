"""工作流规划器，负责将结构化需求生成为最小 DAG 预览"""

from dataclasses import dataclass

from app.agents.templates import get_role_template
from app.core.llm.adapter import LLMAdapter
from app.core.manager.requirement_extractor import RequirementSummary


@dataclass(frozen=True)
class WorkflowNode:
    """工作流节点对象，描述单个角色的任务与依赖"""

    id: str
    template_id: str
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
        selected_template_ids = self.select_template_ids(requirement)
        nodes: list[WorkflowNode] = []

        for index, template_id in enumerate(selected_template_ids, start=1):
            template = get_role_template(template_id)
            depends_on = [nodes[-1].id] if nodes else []
            nodes.append(
                WorkflowNode(
                    id=f"node_{index}",
                    template_id=template.template_id,
                    role=template.role_name,
                    task=self.build_node_task(template.template_id, requirement),
                    tools=template.default_tools,
                    llm=runtime_label,
                    max_retries=template.max_retries,
                    depends_on=depends_on,
                )
            )

        return WorkflowDag(nodes=nodes, execution_mode="serial")

    def select_template_ids(self, requirement: RequirementSummary) -> list[str]:
        """根据需求内容和输出类型选择本轮工作流的角色模板序列"""

        context_text = "\n".join(
            [requirement.goal, requirement.context, *requirement.constraints]
        )
        selected_template_ids = ["pm"]

        if self.needs_frontend(context_text, requirement.output_types):
            selected_template_ids.append("frontend")

        if self.needs_design(context_text, requirement.output_types):
            selected_template_ids.append("designer")

        if self.needs_backend(context_text, requirement.output_types):
            selected_template_ids.append("backend")

        if self.needs_quality(context_text):
            selected_template_ids.append("qa")

        if selected_template_ids == ["pm"]:
            selected_template_ids.append("backend")

        return selected_template_ids

    def needs_frontend(self, context_text: str, output_types: list[str]) -> bool:
        """判断当前需求是否需要前端模板参与"""

        normalized_text = context_text.lower()
        keywords = (
            "前端",
            "页面",
            "界面",
            "网页",
            "交互",
            "组件",
            "frontend",
            "page",
            "ui",
            "web",
            "component",
        )
        return "code" in output_types or any(
            keyword.lower() in normalized_text for keyword in keywords
        )

    def needs_backend(self, context_text: str, output_types: list[str]) -> bool:
        """判断当前需求是否需要后端模板参与"""

        normalized_text = context_text.lower()
        keywords = (
            "后端",
            "接口",
            "API",
            "数据库",
            "服务",
            "流程",
            "执行",
            "backend",
            "service",
            "database",
            "api",
        )
        return "code" in output_types or any(
            keyword.lower() in normalized_text for keyword in keywords
        )

    def needs_design(self, context_text: str, output_types: list[str]) -> bool:
        """判断当前需求是否需要设计模板参与"""

        normalized_text = context_text.lower()
        keywords = (
            "设计",
            "视觉",
            "风格",
            "排版",
            "布局",
            "原型",
            "design",
            "visual",
            "layout",
            "prototype",
        )
        return "image" in output_types or any(
            keyword.lower() in normalized_text for keyword in keywords
        )

    def needs_quality(self, context_text: str) -> bool:
        """判断当前需求是否需要测试模板参与"""

        normalized_text = context_text.lower()
        keywords = (
            "测试",
            "验收",
            "验证",
            "回归",
            "质量",
            "风险",
            "test",
            "qa",
            "acceptance",
            "verify",
            "regression",
            "risk",
        )
        return any(keyword.lower() in normalized_text for keyword in keywords)

    def build_node_task(
        self,
        template_id: str,
        requirement: RequirementSummary,
    ) -> str:
        """根据角色模板生成当前节点的任务说明"""

        output_text = (
            ", ".join(requirement.output_types)
            if requirement.output_types
            else "document"
        )

        if template_id == "pm":
            return (
                "梳理本轮需求目标、约束、范围边界和优先级，"
                f"输出可交接的执行摘要。目标：{requirement.goal}"
            )

        if template_id == "frontend":
            return (
                "根据需求摘要整理页面结构、交互流程、组件拆分和前端实现建议，"
                f"优先覆盖输出类型：{output_text}。"
            )

        if template_id == "backend":
            return (
                "根据需求摘要整理接口、数据结构、执行逻辑和后端实现方案，"
                f"确保可支撑输出类型：{output_text}。"
            )

        if template_id == "designer":
            return (
                "根据需求摘要整理视觉方向、布局层级和设计表达重点，"
                "为后续界面交付提供统一设计说明。"
            )

        if template_id == "qa":
            return (
                "基于前序产出整理测试关注点、风险项、回归范围和验收标准，"
                "输出可直接执行的验证摘要。"
            )

        template = get_role_template(template_id)
        return template.summary
