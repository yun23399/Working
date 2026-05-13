"""示例研究助理插件，提供最小可用的插件角色模板"""

from app.agents.templates.role_templates import RoleTemplate
from app.core.plugins.plugin_loader import PluginBase


def build_plugin() -> PluginBase:
    """构建示例插件对象，供本地插件加载器自动发现"""

    return PluginBase(
        plugin_id="research-helper",
        name="研究助理插件",
        description="为包含调研、竞品和资料整理需求的工作流补充研究助理角色。",
        tools=["file_tool", "api_caller"],
        agent_templates=[
            RoleTemplate(
                template_id="research-analyst",
                role_name="研究助理",
                summary="负责资料检索、竞品整理、证据归纳与对比结论输出。",
                system_prompt=(
                    "你是研究助理，重点关注资料来源、竞品差异、信息可信度、"
                    "关键证据和结构化结论输出。"
                ),
                default_tools=["file_tool", "api_caller"],
                max_retries=2,
                trigger_keywords=["调研", "研究", "竞品", "资料", "research"],
            )
        ],
    )
