"""插件加载器，负责扫描仓库根目录 `plugins/` 并返回可用插件信息"""

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

from app.agents.templates.role_templates import RoleTemplate
from app.config import ROOT_DIR

PLUGIN_ENTRY_FILE = "plugin.py"
PLUGIN_MANIFEST_FILE = "plugin.json"
PLUGINS_ROOT_DIR = ROOT_DIR / "plugins"


class PluginLoadError(Exception):
    """插件加载异常，供上层统一转换为接口错误"""


@dataclass(frozen=True)
class PluginBase:
    """插件基础对象，描述插件的元信息、工具声明和角色模板"""

    plugin_id: str
    name: str
    description: str
    tools: list[str]
    agent_templates: list[RoleTemplate]
    version: str = "1.0.0"


@dataclass(frozen=True)
class LoadedPlugin:
    """已加载插件对象，包含来源路径与启用状态"""

    plugin_id: str
    name: str
    description: str
    version: str
    tools: list[str]
    agent_templates: list[RoleTemplate]
    source_path: str
    is_enabled: bool


def normalize_plugin_id(value: str) -> str:
    """规范化插件编号，避免路径与配置之间的大小写偏差"""

    return "-".join(value.strip().lower().split())


def list_plugin_directories() -> list[Path]:
    """列出插件根目录下的一级插件目录，并展开 `examples/` 子目录"""

    if not PLUGINS_ROOT_DIR.exists():
        return []

    plugin_directories: list[Path] = []
    for item in sorted(PLUGINS_ROOT_DIR.iterdir(), key=lambda path: path.name.lower()):
        if not item.is_dir() or item.name.startswith("."):
            continue
        if item.name == "examples":
            for example_item in sorted(
                item.iterdir(), key=lambda path: path.name.lower()
            ):
                if example_item.is_dir() and not example_item.name.startswith("."):
                    plugin_directories.append(example_item)
            continue
        plugin_directories.append(item)

    return plugin_directories


def load_plugin_manifest(plugin_dir: Path) -> dict[str, str]:
    """读取插件清单文件，供接口展示额外元信息"""

    manifest_path = plugin_dir / PLUGIN_MANIFEST_FILE
    if not manifest_path.exists():
        return {}

    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginLoadError(f"插件清单解析失败：{plugin_dir.name}") from exc


def load_plugin_module(plugin_dir: Path):
    """动态加载插件入口模块，并返回模块对象"""

    module_path = plugin_dir / PLUGIN_ENTRY_FILE
    if not module_path.exists():
        raise PluginLoadError(
            f"插件缺少入口文件：{plugin_dir.name}/{PLUGIN_ENTRY_FILE}"
        )

    module_name = f"app_plugin_{normalize_plugin_id(plugin_dir.name).replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"插件入口加载失败：{plugin_dir.name}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def coerce_role_template(plugin_id: str, template: RoleTemplate) -> RoleTemplate:
    """规范化插件模板编号前缀，并统一标记来源为 `plugin`"""

    next_template_id = template.template_id
    plugin_prefix = f"plugin:{plugin_id}:"
    if not next_template_id.startswith(plugin_prefix):
        next_template_id = f"{plugin_prefix}{template.template_id}"

    return RoleTemplate(
        template_id=next_template_id,
        role_name=template.role_name,
        summary=template.summary,
        system_prompt=template.system_prompt,
        default_tools=template.default_tools,
        max_retries=template.max_retries,
        source="plugin",
        trigger_keywords=template.trigger_keywords,
        is_enabled=template.is_enabled,
    )


def load_plugin_from_directory(
    plugin_dir: Path,
    enabled_plugin_ids: set[str],
) -> LoadedPlugin:
    """从插件目录加载单个插件，并附带启用状态"""

    module = load_plugin_module(plugin_dir)
    if not hasattr(module, "build_plugin"):
        raise PluginLoadError(f"插件缺少 build_plugin 方法：{plugin_dir.name}")

    plugin = module.build_plugin()
    if not isinstance(plugin, PluginBase):
        raise PluginLoadError(f"插件返回值不是 PluginBase：{plugin_dir.name}")

    manifest = load_plugin_manifest(plugin_dir)
    plugin_id = normalize_plugin_id(plugin.plugin_id or plugin_dir.name)
    agent_templates = [
        coerce_role_template(plugin_id, template) for template in plugin.agent_templates
    ]

    return LoadedPlugin(
        plugin_id=plugin_id,
        name=plugin.name,
        description=plugin.description,
        version=str(manifest.get("version") or plugin.version),
        tools=plugin.tools,
        agent_templates=agent_templates,
        source_path=str(plugin_dir),
        is_enabled=plugin_id in enabled_plugin_ids,
    )


def list_loaded_plugins(enabled_plugin_ids: set[str]) -> list[LoadedPlugin]:
    """扫描并加载全部本地插件，返回前端和工作流可消费的结构"""

    return [
        load_plugin_from_directory(plugin_dir, enabled_plugin_ids)
        for plugin_dir in list_plugin_directories()
    ]


def list_enabled_plugin_templates(enabled_plugin_ids: set[str]) -> list[RoleTemplate]:
    """返回当前启用插件提供的全部角色模板，供工作流规划阶段并入"""

    templates: list[RoleTemplate] = []
    for plugin in list_loaded_plugins(enabled_plugin_ids):
        if not plugin.is_enabled:
            continue
        templates.extend(plugin.agent_templates)
    return templates
