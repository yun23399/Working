"""Agent 生成器，负责按工作流节点动态创建最小执行 Agent"""

from app.agents.agent_runner import GenericTaskAgent
from app.core.manager.workflow_planner import WorkflowNode


class AgentSpawner:
    """最小 Agent 生成器，根据节点配置创建通用执行 Agent"""

    def spawn(self, node: WorkflowNode) -> GenericTaskAgent:
        """按节点角色与重试配置创建最小可执行 Agent"""

        return GenericTaskAgent(
            role=node.role,
            llm_model=node.llm,
            max_retries=node.max_retries,
        )
