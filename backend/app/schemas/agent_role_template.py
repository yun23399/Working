"""用户自定义 Agent 角色模板的请求与响应模型"""

from datetime import datetime
from typing import Literal

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


class AgentRoleTemplateExportItemSchema(AgentRoleTemplateResponseSchema):
    """导出文件中的单个角色模板条目"""


class AgentRoleTemplateExportBundleSchema(BaseModel):
    """角色模板导出包，便于跨账号或跨环境导入复用"""

    version: Literal["1.0"] = "1.0"
    exported_at: datetime
    template_count: int = Field(ge=0)
    templates: list[AgentRoleTemplateExportItemSchema] = Field(default_factory=list)


class AgentRoleTemplateImportItemSchema(AgentRoleTemplateBaseSchema):
    """角色模板导入条目，兼容导出文件中的模板定义"""

    template_id: str | None = None


class AgentRoleTemplateImportBundleSchema(BaseModel):
    """角色模板导入包，描述导入版本和模板列表"""

    version: Literal["1.0"] = "1.0"
    templates: list[AgentRoleTemplateImportItemSchema] = Field(default_factory=list)


class AgentRoleTemplateImportRequestSchema(BaseModel):
    """角色模板导入请求，描述冲突处理策略与导入内容"""

    conflict_strategy: Literal["skip", "overwrite"] = "skip"
    bundle: AgentRoleTemplateImportBundleSchema


class AgentRoleTemplateImportResultItemSchema(BaseModel):
    """单个角色模板导入结果条目，供前端展示明细"""

    role_name: str
    template_id: str | None = None
    status: Literal["created", "updated", "skipped"]
    message: str


class AgentRoleTemplateImportResponseSchema(BaseModel):
    """角色模板导入结果汇总"""

    total_count: int = Field(ge=0)
    created_count: int = Field(ge=0)
    updated_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    results: list[AgentRoleTemplateImportResultItemSchema] = Field(default_factory=list)
