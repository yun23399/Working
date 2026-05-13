"""工作流运行日志服务层，负责读取共享工作区中的结构化日志文件"""

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowRuntimeLogSchema
from app.workflow.workspace import WorkflowWorkspace


def list_workflow_runtime_logs(
    workflow: Workflow,
    limit: int = 200,
) -> list[WorkflowRuntimeLogSchema]:
    """返回当前工作流最近的运行日志列表，供日志面板回填和过滤"""

    workspace = WorkflowWorkspace(workflow)
    return [
        WorkflowRuntimeLogSchema(**item)
        for item in workspace.load_runtime_logs(limit=limit)
    ]
