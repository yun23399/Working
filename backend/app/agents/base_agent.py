"""Agent 基类定义，统一封装节点执行接口"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentTask:
    """Agent 任务对象，描述角色收到的最小执行上下文"""

    workflow_id: int
    conversation_id: int
    node_id: str
    role: str
    task: str
    context: str


@dataclass(frozen=True)
class AgentResult:
    """Agent 执行结果对象，返回摘要文本供日志和持久化使用"""

    summary: str
    token_count: int


class BaseAgent:
    """Agent 基类，约束所有角色的最小执行接口"""

    role: str
    llm_model: str
    max_retries: int

    def __init__(self, role: str, llm_model: str, max_retries: int) -> None:
        """初始化 Agent 基础属性，供运行时与日志统一读取"""

        self.role = role
        self.llm_model = llm_model
        self.max_retries = max_retries

    async def run(self, task: AgentTask) -> AgentResult:
        """执行具体任务，子类必须实现"""

        raise NotImplementedError
