"""工作流预览模块的请求与响应模型定义"""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowPreviewRequestSchema(BaseModel):
    """工作流预览请求模型，允许指定是否强制重新规划"""

    force_replan: bool = False


class RequirementSummarySchema(BaseModel):
    """结构化需求摘要模型，描述目标、约束与产出类型"""

    goal: str
    constraints: list[str]
    output_types: list[str]
    context: str


class WorkflowNodeSchema(BaseModel):
    """工作流节点模型，描述角色、任务和依赖关系"""

    id: str
    template_id: str
    role: str
    task: str
    tools: list[str]
    llm: str
    max_retries: int = Field(ge=0)
    depends_on: list[str]
    runtime_status: str | None = None


class WorkflowDagSchema(BaseModel):
    """工作流 DAG 模型，描述节点列表与执行模式"""

    nodes: list[WorkflowNodeSchema]
    execution_mode: str


class WorkflowExecutionLogSchema(BaseModel):
    """工作流执行日志模型，描述节点完成后的最小交接摘要"""

    node_id: str
    role: str
    summary: str
    status: str
    artifacts: list[str] = []


class WorkflowHandoffSchema(BaseModel):
    """工作流交接记录模型，描述节点之间的共享工作区交付信息"""

    from_agent: str
    to_agent: str
    summary: str
    artifacts: list[str]
    created_at: str


class WorkflowWorkspaceStateSchema(BaseModel):
    """工作流共享工作区状态模型，描述当前目录、进度和产出物快照"""

    workspace_path: str
    status: str
    progress: int
    active_node_id: str | None
    artifacts: list[str]
    updated_at: str


class WorkflowPreviewResponseSchema(BaseModel):
    """工作流预览响应模型，返回需求摘要和 DAG 结果"""

    workflow_id: int
    conversation_id: int
    status: str
    progress: int
    requirement: RequirementSummarySchema
    dag: WorkflowDagSchema
    execution_logs: list[WorkflowExecutionLogSchema]
    workspace: WorkflowWorkspaceStateSchema
    handoff_logs: list[WorkflowHandoffSchema]
    created_at: datetime
    updated_at: datetime
