"""Agent 运行时，负责基于统一 LLM 适配器执行节点任务"""

from app.agents.base_agent import AgentResult, AgentTask, BaseAgent
from app.agents.templates import get_role_template
from app.core.llm.adapter import ChatMessage, LLMAdapter


class GenericTaskAgent(BaseAgent):
    """通用任务 Agent，使用角色和任务描述生成最小执行摘要"""

    def __init__(
        self,
        role: str,
        llm_model: str,
        max_retries: int,
        template_id: str,
    ) -> None:
        """初始化通用 Agent，保留当前节点的角色与重试信息"""

        super().__init__(role=role, llm_model=llm_model, max_retries=max_retries)
        self.adapter = LLMAdapter()
        self.template = get_role_template(template_id)

    def build_messages(self, task: AgentTask) -> list[ChatMessage]:
        """构造节点执行所需的最小上下文消息"""

        return [
            ChatMessage(
                role="system",
                content=(
                    "你是多智能体编排平台中的执行 Agent。"
                    f"当前角色是：{task.role}。"
                    f"角色职责：{self.template.summary}。"
                    f"{self.template.system_prompt}"
                    "请根据任务描述输出简洁、明确、可交接的执行结果摘要。"
                    "本阶段只返回文本结果，不调用工具，不输出额外解释。"
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    f"工作流节点：{task.node_id}\n"
                    f"模板编号：{self.template.template_id}\n"
                    f"任务描述：{task.task}\n"
                    f"上下文：{task.context}"
                ),
            ),
        ]

    async def run(self, task: AgentTask) -> AgentResult:
        """执行节点任务并返回完整文本摘要"""

        parts: list[str] = []
        async for token in self.adapter.stream_chat(self.build_messages(task)):
            parts.append(token)

        content = "".join(parts).strip()
        return AgentResult(summary=content, token_count=max(len(parts), 1))
