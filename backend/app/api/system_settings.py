"""系统运行配置路由，提供并发上限与 LLM 设置接口"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.llm.providers import LLMConfigurationError
from app.models.user import User
from app.schemas.system_settings import (
    SystemLlmSettingsResponseSchema,
    SystemLlmSettingsTestResponseSchema,
    SystemLlmSettingsTestSchema,
    SystemLlmSettingsUpdateSchema,
    SystemRuntimeSettingsResponseSchema,
    SystemRuntimeSettingsUpdateSchema,
)
from app.services.system_settings_service import (
    get_system_llm_settings,
    get_system_runtime_settings,
    test_system_llm_settings,
    update_max_concurrent_workflows,
    update_system_llm_settings,
)

router = APIRouter(prefix="/api/system-settings", tags=["system-settings"])


@router.get("/llm", response_model=SystemLlmSettingsResponseSchema)
def get_system_llm_settings_endpoint(
    _: User = Depends(get_current_user),
) -> SystemLlmSettingsResponseSchema:
    """返回当前 LLM 设置，供设置页展示 API 地址、模型与密钥状态"""

    try:
        return get_system_llm_settings()
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "读取 LLM 设置失败",
                "code": "GET_SYSTEM_LLM_SETTINGS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.put("/llm", response_model=SystemLlmSettingsResponseSchema)
def update_system_llm_settings_endpoint(
    payload: SystemLlmSettingsUpdateSchema,
    _: User = Depends(get_current_user),
) -> SystemLlmSettingsResponseSchema:
    """更新当前 LLM 设置，并让新的提供商与模型配置立即生效"""

    try:
        return update_system_llm_settings(payload)
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "LLM 设置不合法",
                "code": "INVALID_LLM_SETTINGS",
                "detail": str(exc),
            },
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "更新 LLM 设置失败",
                "code": "UPDATE_SYSTEM_LLM_SETTINGS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post("/llm/test", response_model=SystemLlmSettingsTestResponseSchema)
async def test_system_llm_settings_endpoint(
    payload: SystemLlmSettingsTestSchema,
    _: User = Depends(get_current_user),
) -> SystemLlmSettingsTestResponseSchema:
    """使用临时参数测试第三方 LLM 接口连通性与最小响应能力"""

    try:
        return await test_system_llm_settings(payload)
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "LLM 测试配置不合法",
                "code": "INVALID_LLM_TEST_SETTINGS",
                "detail": str(exc),
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "LLM 连通性测试失败",
                "code": "TEST_SYSTEM_LLM_SETTINGS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get("/runtime", response_model=SystemRuntimeSettingsResponseSchema)
def get_system_runtime_settings_endpoint(
    _: User = Depends(get_current_user),
) -> SystemRuntimeSettingsResponseSchema:
    """返回当前系统运行配置，用于设置页展示并发上限和活动槽位"""

    try:
        return get_system_runtime_settings()
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "读取系统运行配置失败",
                "code": "GET_SYSTEM_RUNTIME_SETTINGS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.put("/runtime", response_model=SystemRuntimeSettingsResponseSchema)
def update_system_runtime_settings_endpoint(
    payload: SystemRuntimeSettingsUpdateSchema,
    _: User = Depends(get_current_user),
) -> SystemRuntimeSettingsResponseSchema:
    """更新当前系统运行配置，并让新的并发上限实时生效"""

    try:
        return update_max_concurrent_workflows(payload.max_concurrent_workflows)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "更新系统运行配置失败",
                "code": "UPDATE_SYSTEM_RUNTIME_SETTINGS_FAILED",
                "detail": str(exc),
            },
        ) from exc
