"""系统运行配置相关的请求与响应模型"""

from pydantic import BaseModel, Field


class SystemRuntimeSettingsResponseSchema(BaseModel):
    """系统运行配置响应模型，返回当前并发上限与活动槽位信息"""

    max_concurrent_workflows: int = Field(ge=1, le=10)
    active_workflow_count: int = Field(ge=0)
    remaining_slots: int = Field(ge=0)
    is_limit_reached: bool


class SystemRuntimeSettingsUpdateSchema(BaseModel):
    """系统运行配置更新模型，当前仅支持修改工作流并发上限"""

    max_concurrent_workflows: int = Field(ge=1, le=10)
