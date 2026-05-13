"""LLM 提供商配置解析模块，统一管理模型与连接参数"""

from dataclasses import dataclass
from typing import Literal

from app.config import settings

ProviderName = Literal["openai", "anthropic", "ollama"]
SUPPORTED_PROVIDERS = {"openai", "anthropic", "ollama", "auto"}
KNOWN_PROVIDER_PREFIXES = {"openai", "anthropic", "ollama", "ollama_chat"}


class LLMConfigurationError(Exception):
    """LLM 配置异常，用于提示缺失或冲突的模型参数"""


@dataclass(frozen=True)
class LLMProviderConfig:
    """统一的 LLM 运行配置，供适配器直接消费"""

    provider: ProviderName
    model: str
    api_key: str | None
    base_url: str | None
    timeout_seconds: int


def normalize_provider_name(provider: str) -> str:
    """标准化提供商名称，统一处理大小写和空白字符"""

    return provider.strip().lower()


def split_provider_prefixed_model(model: str) -> tuple[str | None, str]:
    """拆解带前缀的模型名，便于校验提供商与模型是否一致"""

    normalized_model = model.strip()
    if "/" not in normalized_model:
        return None, normalized_model

    provider_prefix, raw_model = normalized_model.split("/", 1)
    provider_name = normalize_provider_name(provider_prefix)
    if provider_name in KNOWN_PROVIDER_PREFIXES:
        return provider_name, raw_model.strip()
    return None, normalized_model


def is_provider_prefix_compatible(
    provider: ProviderName, model_provider: str | None
) -> bool:
    """判断模型前缀与目标提供商是否兼容，兼容 Ollama 的双前缀写法"""

    if model_provider is None:
        return True
    if provider == "ollama":
        return model_provider in {"ollama", "ollama_chat"}
    return model_provider == provider


def build_default_model(provider: ProviderName) -> str:
    """根据提供商返回默认模型名称，减少本地启动配置成本"""

    if provider == "openai":
        return "gpt-4.1-mini"
    if provider == "anthropic":
        return "claude-3-5-sonnet-latest"
    return "qwen2.5-coder:3b"


def resolve_provider_name() -> ProviderName:
    """根据环境变量选择当前应使用的 LLM 提供商"""

    requested_provider = normalize_provider_name(settings.llm_provider)
    if requested_provider not in SUPPORTED_PROVIDERS:
        raise LLMConfigurationError(
            "LLM_PROVIDER 仅支持 openai、anthropic、ollama 或 auto"
        )

    if requested_provider == "openai":
        if not settings.openai_api_key.strip():
            raise LLMConfigurationError(
                "已指定 OPENAI 提供商，但 OPENAI_API_KEY 未配置"
            )
        return "openai"

    if requested_provider == "anthropic":
        if not settings.anthropic_api_key.strip():
            raise LLMConfigurationError(
                "已指定 Anthropic 提供商，但 ANTHROPIC_API_KEY 未配置"
            )
        return "anthropic"

    if requested_provider == "ollama":
        return "ollama"

    if settings.openai_api_key.strip():
        return "openai"
    if settings.anthropic_api_key.strip():
        return "anthropic"
    return "ollama"


def resolve_model_name(provider: ProviderName) -> str:
    """解析当前提供商对应的最终模型名，并处理前缀冲突"""

    configured_model = settings.llm_model.strip() or build_default_model(provider)
    model_provider, model_name = split_provider_prefixed_model(configured_model)

    if not is_provider_prefix_compatible(provider, model_provider):
        raise LLMConfigurationError(
            "LLM_MODEL 的提供商前缀与 LLM_PROVIDER 不一致，请统一配置"
        )

    normalized_model_name = model_name.strip()
    if not normalized_model_name:
        raise LLMConfigurationError("LLM_MODEL 不能为空")

    model_prefix = "ollama_chat" if provider == "ollama" else provider
    return f"{model_prefix}/{normalized_model_name}"


def resolve_provider_config() -> LLMProviderConfig:
    """汇总当前运行所需的 LLM 配置，供统一适配层调用"""

    provider = resolve_provider_name()
    model = resolve_model_name(provider)
    api_key: str | None = None
    base_url: str | None = None

    if provider == "openai":
        api_key = settings.openai_api_key.strip()
        base_url = settings.openai_base_url.strip().rstrip("/") or None
    elif provider == "anthropic":
        api_key = settings.anthropic_api_key.strip()
    else:
        base_url = settings.ollama_base_url.rstrip("/")

    return LLMProviderConfig(
        provider=provider,
        model=model,
        api_key=api_key or None,
        base_url=base_url,
        timeout_seconds=settings.llm_timeout_seconds,
    )
