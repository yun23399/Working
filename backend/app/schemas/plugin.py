"""插件管理相关的响应模型定义"""

from pydantic import BaseModel


class PluginTemplateSchema(BaseModel):
    """插件角色模板摘要模型，供设置页展示插件能力范围"""

    template_id: str
    role_name: str
    summary: str
    trigger_keywords: list[str]
    default_tools: list[str]


class PluginSettingsResponseSchema(BaseModel):
    """插件设置响应模型，描述插件元信息与启停状态"""

    plugin_id: str
    name: str
    description: str
    version: str
    tools: list[str]
    agent_templates: list[PluginTemplateSchema]
    source_path: str
    is_enabled: bool


class PluginSettingsUpdateSchema(BaseModel):
    """插件启停更新模型"""

    is_enabled: bool
