"""系统运行配置服务层，负责读取和更新 `.env` 中的运行参数"""

import os
from pathlib import Path

from app.config import ROOT_ENV_FILE, reload_settings, settings
from app.core.llm.adapter import ChatMessage, LLMAdapter
from app.core.llm.providers import (
    SUPPORTED_PROVIDERS,
    LLMConfigurationError,
    LLMProviderConfig,
    normalize_provider_name,
)
from app.core.runtime.workflow_concurrency import workflow_concurrency_controller
from app.schemas.system_settings import (
    SystemLlmSettingsResponseSchema,
    SystemLlmSettingsTestResponseSchema,
    SystemLlmSettingsTestSchema,
    SystemLlmSettingsUpdateSchema,
    SystemRuntimeSettingsResponseSchema,
)

ENV_MAX_CONCURRENT_WORKFLOWS = "MAX_CONCURRENT_WORKFLOWS"
ENV_ENABLED_PLUGINS = "ENABLED_PLUGINS"
ENV_LLM_PROVIDER = "LLM_PROVIDER"
ENV_LLM_MODEL = "LLM_MODEL"
ENV_LLM_TIMEOUT_SECONDS = "LLM_TIMEOUT_SECONDS"
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_OPENAI_BASE_URL = "OPENAI_BASE_URL"
ENV_MANAGER_READINESS_THRESHOLD = "MANAGER_READINESS_THRESHOLD"


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


def normalize_llm_provider(provider: str) -> str:
    """标准化并校验当前 LLM 提供商名称"""

    normalized_provider = normalize_provider_name(provider)
    if normalized_provider not in SUPPORTED_PROVIDERS:
        raise LLMConfigurationError(
            "LLM_PROVIDER 仅支持 openai、anthropic、ollama 或 auto"
        )
    return normalized_provider


def get_system_llm_settings() -> SystemLlmSettingsResponseSchema:
    """返回当前 LLM 设置快照，供前端设置页展示与回填"""

    return SystemLlmSettingsResponseSchema(
        provider=settings.llm_provider,
        model=settings.llm_model or "gpt-4.1-mini",
        base_url=settings.openai_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        api_key_configured=bool(settings.openai_api_key.strip()),
        manager_readiness_threshold=settings.manager_readiness_threshold,
    )


def update_system_llm_settings(
    payload: SystemLlmSettingsUpdateSchema,
) -> SystemLlmSettingsResponseSchema:
    """更新根目录 `.env` 中的 LLM 设置，并让当前进程立即生效"""

    provider = normalize_llm_provider(payload.provider)
    model = payload.model.strip()
    if not model:
        raise LLMConfigurationError("LLM_MODEL 不能为空")

    base_url = payload.base_url.strip().rstrip("/")
    api_key = payload.api_key.strip()

    upsert_env_value(ROOT_ENV_FILE, ENV_LLM_PROVIDER, provider)
    upsert_env_value(ROOT_ENV_FILE, ENV_LLM_MODEL, model)
    upsert_env_value(
        ROOT_ENV_FILE,
        ENV_LLM_TIMEOUT_SECONDS,
        str(payload.timeout_seconds),
    )
    upsert_env_value(ROOT_ENV_FILE, ENV_OPENAI_BASE_URL, base_url)
    upsert_env_value(
        ROOT_ENV_FILE,
        ENV_MANAGER_READINESS_THRESHOLD,
        str(payload.manager_readiness_threshold),
    )

    if api_key:
        upsert_env_value(ROOT_ENV_FILE, ENV_OPENAI_API_KEY, api_key)
        os.environ[ENV_OPENAI_API_KEY] = api_key

    os.environ[ENV_LLM_PROVIDER] = provider
    os.environ[ENV_LLM_MODEL] = model
    os.environ[ENV_LLM_TIMEOUT_SECONDS] = str(payload.timeout_seconds)
    os.environ[ENV_OPENAI_BASE_URL] = base_url
    os.environ[ENV_MANAGER_READINESS_THRESHOLD] = str(
        payload.manager_readiness_threshold
    )
    reload_settings()
    return get_system_llm_settings()


def build_test_provider_config(
    payload: SystemLlmSettingsTestSchema,
) -> LLMProviderConfig:
    """根据测试请求构造临时 LLM 配置，避免污染当前全局设置"""

    provider = normalize_llm_provider(payload.provider)
    model = payload.model.strip()
    if not model:
        raise LLMConfigurationError("LLM_MODEL 不能为空")

    base_url = payload.base_url.strip().rstrip("/") or None
    api_key = payload.api_key.strip() or None

    if provider == "openai" and api_key is None and settings.openai_api_key.strip():
        api_key = settings.openai_api_key.strip()

    if (
        provider == "anthropic"
        and api_key is None
        and settings.anthropic_api_key.strip()
    ):
        api_key = settings.anthropic_api_key.strip()

    if provider == "openai" and api_key is None:
        raise LLMConfigurationError("测试 OPENAI 兼容接口时必须提供 API Key")

    if provider == "anthropic" and api_key is None:
        raise LLMConfigurationError("测试 Anthropic 接口时必须提供 API Key")

    if provider == "ollama" and base_url is None:
        base_url = settings.ollama_base_url.rstrip("/")

    model_prefix = "ollama_chat" if provider == "ollama" else provider
    normalized_model = model.split("/", 1)[-1].strip()

    return LLMProviderConfig(
        provider=provider,  # type: ignore[arg-type]
        model=f"{model_prefix}/{normalized_model}",
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=payload.timeout_seconds,
    )


async def test_system_llm_settings(
    payload: SystemLlmSettingsTestSchema,
) -> SystemLlmSettingsTestResponseSchema:
    """使用临时配置发起最小模型请求，验证第三方接口是否可用"""

    provider_config = build_test_provider_config(payload)
    adapter = LLMAdapter(provider_config=provider_config)
    messages = [
        ChatMessage(
            role="system",
            content="你是系统配置测试助手，请只返回一句简短中文确认。",
        ),
        ChatMessage(role="user", content="请回复：连接测试成功。"),
    ]
    content_parts: list[str] = []

    async for token in adapter.stream_chat(messages):
        content_parts.append(token)
        joined_content = "".join(content_parts).strip()
        if joined_content:
            return SystemLlmSettingsTestResponseSchema(
                success=True,
                runtime_label=adapter.get_runtime_label(),
                message=joined_content[:120],
            )

    raise LLMConfigurationError("模型未返回可用内容，请检查地址、密钥或模型名称")
