"""系统运行配置服务层，负责读取和更新 `.env` 中的运行参数"""

import os
from pathlib import Path

from app.config import ROOT_ENV_FILE, reload_settings
from app.core.runtime.workflow_concurrency import workflow_concurrency_controller
from app.schemas.system_settings import SystemRuntimeSettingsResponseSchema

ENV_MAX_CONCURRENT_WORKFLOWS = "MAX_CONCURRENT_WORKFLOWS"
ENV_ENABLED_PLUGINS = "ENABLED_PLUGINS"


def read_env_lines(env_path: Path) -> list[str]:
    """读取 `.env` 文件内容，若文件不存在则返回空列表"""

    if not env_path.exists():
        return []
    return env_path.read_text(encoding="utf-8").splitlines()


def write_env_lines(env_path: Path, lines: list[str]) -> None:
    """将更新后的 `.env` 内容写回磁盘，统一使用 UTF-8 编码"""

    env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def upsert_env_value(env_path: Path, key: str, value: str) -> None:
    """更新或追加指定环境变量键值，保持其余配置内容不变"""

    lines = read_env_lines(env_path)
    next_lines: list[str] = []
    matched = False

    for line in lines:
        if line.startswith(f"{key}="):
            next_lines.append(f"{key}={value}")
            matched = True
            continue

        next_lines.append(line)

    if not matched:
        next_lines.append(f"{key}={value}")

    write_env_lines(env_path, next_lines)


def get_system_runtime_settings() -> SystemRuntimeSettingsResponseSchema:
    """返回当前系统运行配置快照，供设置页和执行链路展示"""

    return SystemRuntimeSettingsResponseSchema(
        **workflow_concurrency_controller.build_runtime_snapshot()
    )


def update_max_concurrent_workflows(
    max_concurrent_workflows: int,
) -> SystemRuntimeSettingsResponseSchema:
    """更新 `.env` 中的工作流并发上限，并让当前进程立即生效"""

    upsert_env_value(
        ROOT_ENV_FILE,
        ENV_MAX_CONCURRENT_WORKFLOWS,
        str(max_concurrent_workflows),
    )
    os.environ[ENV_MAX_CONCURRENT_WORKFLOWS] = str(max_concurrent_workflows)
    reload_settings()
    return get_system_runtime_settings()
