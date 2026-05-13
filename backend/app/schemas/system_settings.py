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


class SystemLlmSettingsResponseSchema(BaseModel):
    """LLM 设置响应模型，返回当前提供商、模型与密钥状态"""

    provider: str
    model: str
    base_url: str
    timeout_seconds: int = Field(ge=5, le=300)
    api_key_configured: bool
    manager_readiness_threshold: int = Field(ge=50, le=100)


class SystemLlmSettingsUpdateSchema(BaseModel):
    """LLM 设置更新模型，允许在设置页保存第三方模型配置"""

    provider: str = Field(min_length=1, max_length=20)
    model: str = Field(min_length=1, max_length=120)
    base_url: str = Field(default="", max_length=255)
    api_key: str = Field(default="", max_length=255)
    timeout_seconds: int = Field(ge=5, le=300)
    manager_readiness_threshold: int = Field(ge=50, le=100)


class SystemLlmSettingsTestSchema(BaseModel):
    """LLM 设置测试请求模型，支持用临时配置做连通性验证"""

    provider: str = Field(min_length=1, max_length=20)
    model: str = Field(min_length=1, max_length=120)
    base_url: str = Field(default="", max_length=255)
    api_key: str = Field(default="", max_length=255)
    timeout_seconds: int = Field(ge=5, le=300)


class SystemLlmSettingsTestResponseSchema(BaseModel):
    """LLM 设置测试响应模型，返回连通性和运行时标签"""

    success: bool
    runtime_label: str
    message: str
