"""Agent 生成器，负责按工作流节点动态创建最小执行 Agent"""

from app.agents.agent_runner import GenericTaskAgent
from app.agents.templates.role_templates import RoleTemplate
from app.core.manager.workflow_planner import WorkflowNode


class AgentSpawner:
    """最小 Agent 生成器，根据节点配置创建通用执行 Agent"""

    def build_role_template_snapshot(self, node: WorkflowNode) -> RoleTemplate:
        """根据工作流节点构造执行阶段可直接消费的模板快照"""

        return RoleTemplate(
            template_id=node.template_id,
            role_name=node.role,
            summary=node.template_summary,
            system_prompt=node.template_system_prompt,
            default_tools=node.tools,
            max_retries=node.max_retries,
            source=node.template_source,
            trigger_keywords=node.trigger_keywords,
        )

    def spawn(self, node: WorkflowNode) -> GenericTaskAgent:
        """按节点角色与重试配置创建最小可执行 Agent"""

        return GenericTaskAgent(
            role=node.role,
            llm_model=node.llm,
            max_retries=node.max_retries,
            template=self.build_role_template_snapshot(node),
        )
