"""用户自定义 Agent 角色模板的请求与响应模型"""

from datetime import datetime

from pydantic import BaseModel, Field


class AgentRoleTemplateBaseSchema(BaseModel):
    """自定义角色模板公共字段模型"""

    role_name: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=255)
    system_prompt: str = Field(min_length=1)
    trigger_keywords: list[str] = Field(default_factory=list)
    default_tools: list[str] = Field(default_factory=list)
    max_retries: int = Field(default=2, ge=0, le=5)
    is_enabled: bool = True


class AgentRoleTemplateCreateSchema(AgentRoleTemplateBaseSchema):
    """创建自定义角色模板请求模型"""


class AgentRoleTemplateUpdateSchema(AgentRoleTemplateBaseSchema):
    """更新自定义角色模板请求模型"""


class AgentRoleTemplateResponseSchema(AgentRoleTemplateBaseSchema):
    """自定义角色模板响应模型"""

    template_id: str
    created_at: datetime
    updated_at: datetime
