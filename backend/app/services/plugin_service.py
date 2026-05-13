"""插件服务层，负责插件扫描、启停持久化与工作流模板汇总"""

from app.agents.templates.role_templates import RoleTemplate
from app.core.plugins.plugin_loader import (
    LoadedPlugin,
    list_enabled_plugin_templates,
    list_loaded_plugins,
    normalize_plugin_id,
)
from app.schemas.plugin import PluginSettingsResponseSchema, PluginTemplateSchema
from app.services.system_settings_service import (
    ENV_ENABLED_PLUGINS,
    ROOT_ENV_FILE,
    upsert_env_value,
)


class PluginNotFoundError(Exception):
    """插件不存在异常"""


def parse_enabled_plugin_ids(value: str) -> set[str]:
    """将环境变量中的启用插件配置解析为编号集合"""

    return {
        normalize_plugin_id(item)
        for item in value.split(",")
        if normalize_plugin_id(item)
    }


def serialize_enabled_plugin_ids(plugin_ids: set[str]) -> str:
    """将启用插件编号集合序列化为稳定的逗号分隔字符串"""

    return ",".join(sorted(plugin_ids))


def get_enabled_plugin_ids_from_env() -> set[str]:
    """读取当前 `.env` 中配置的启用插件编号集合"""

    from app.config import settings

    return parse_enabled_plugin_ids(settings.enabled_plugins)


def loaded_plugin_to_response(plugin: LoadedPlugin) -> PluginSettingsResponseSchema:
    """将运行时插件对象转换为接口响应结构"""

    return PluginSettingsResponseSchema(
        plugin_id=plugin.plugin_id,
        name=plugin.name,
        description=plugin.description,
        version=plugin.version,
        tools=plugin.tools,
        agent_templates=[
            PluginTemplateSchema(
                template_id=template.template_id,
                role_name=template.role_name,
                summary=template.summary,
                trigger_keywords=template.trigger_keywords or [],
                default_tools=template.default_tools,
            )
            for template in plugin.agent_templates
        ],
        source_path=plugin.source_path,
        is_enabled=plugin.is_enabled,
    )


def list_plugin_settings() -> list[PluginSettingsResponseSchema]:
    """返回当前本地已安装插件列表，供设置页展示和管理"""

    enabled_plugin_ids = get_enabled_plugin_ids_from_env()
    return [
        loaded_plugin_to_response(plugin)
        for plugin in list_loaded_plugins(enabled_plugin_ids)
    ]


def update_plugin_enabled_state(
    plugin_id: str,
    is_enabled: bool,
) -> PluginSettingsResponseSchema:
    """更新指定插件的启停状态，并持久化到根目录 `.env`"""

    normalized_plugin_id = normalize_plugin_id(plugin_id)
    enabled_plugin_ids = get_enabled_plugin_ids_from_env()
    plugin_map = {
        plugin.plugin_id: plugin for plugin in list_loaded_plugins(enabled_plugin_ids)
    }
    plugin = plugin_map.get(normalized_plugin_id)
    if plugin is None:
        raise PluginNotFoundError(plugin_id)

    if is_enabled:
        enabled_plugin_ids.add(normalized_plugin_id)
    else:
        enabled_plugin_ids.discard(normalized_plugin_id)

    upsert_env_value(
        ROOT_ENV_FILE,
        ENV_ENABLED_PLUGINS,
        serialize_enabled_plugin_ids(enabled_plugin_ids),
    )

    from app.config import reload_settings

    reload_settings()

    refreshed_plugin_map = {
        item.plugin_id: item
        for item in list_loaded_plugins(get_enabled_plugin_ids_from_env())
    }
    refreshed_plugin = refreshed_plugin_map.get(normalized_plugin_id)
    if refreshed_plugin is None:
        raise PluginNotFoundError(plugin_id)
    return loaded_plugin_to_response(refreshed_plugin)


def list_workflow_plugin_templates() -> list[RoleTemplate]:
    """返回当前启用插件的角色模板，供工作流规划阶段注入"""

    return list_enabled_plugin_templates(get_enabled_plugin_ids_from_env())
