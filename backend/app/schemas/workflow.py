"""工作流预览模块的请求与响应模型定义"""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowPreviewRequestSchema(BaseModel):
    """工作流预览请求模型，允许指定是否强制重新规划"""

    force_replan: bool = False
    pause_after_nodes: list[str] = []


class WorkflowControlRequestSchema(BaseModel):
    """工作流控制请求模型，描述暂停、恢复、中断或改向操作"""

    action: str
    redirect_instruction: str = ""


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
    template_source: str = "builtin"
    template_summary: str
    role: str
    task: str
    tools: list[str]
    llm: str
    max_retries: int = Field(ge=0)
    depends_on: list[str]
    trigger_keywords: list[str] = []
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
    pause_after_nodes: list[str] = []


class WorkflowProjectMemoryErrorSchema(BaseModel):
    """项目级记忆中的最近错误摘要"""

    workflow_id: int
    node_id: str
    role: str
    error_message: str
    recovery_suggestion: str
    updated_at: str


class WorkflowProjectMemorySchema(BaseModel):
    """项目级记忆响应模型，描述对话级共享长期上下文"""

    memory_path: str
    latest_goal: str
    active_constraints: list[str]
    key_points: list[str]
    artifacts: list[str]
    workflow_count: int
    latest_error: WorkflowProjectMemoryErrorSchema | None = None
    updated_at: str


class WorkflowArtifactSchema(BaseModel):
    """工作流产物描述模型，供前端按类型渲染预览组件"""

    name: str
    relative_path: str
    preview_type: str
    mime_type: str
    size_bytes: int
    updated_at: str


class WorkflowRunSchema(BaseModel):
    """工作流运行状态模型，描述当前轮次与断点控制信息"""

    run_id: int | None
    status: str
    control_signal: str
    checkpoint_node_id: str | None
    redirect_instruction: str
    saved_at: str | None


class WorkflowErrorReportSchema(BaseModel):
    """工作流错误报告模型，描述失败节点、回滚信息与恢复建议"""

    failed_node_id: str
    failed_role: str
    task: str
    error_message: str
    retry_count: int
    max_retries: int
    can_retry: bool
    upstream_node_id: str | None
    upstream_role: str
    rollback_checkpoint_node_id: str | None
    rollback_progress: int
    recovery_suggestion: str | None = None


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
    project_memory: WorkflowProjectMemorySchema
    handoff_logs: list[WorkflowHandoffSchema]
    workflow_run: WorkflowRunSchema
    error_report: WorkflowErrorReportSchema | None = None
    created_at: datetime
    updated_at: datetime
