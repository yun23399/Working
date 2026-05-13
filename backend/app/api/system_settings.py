"""系统运行配置路由，提供并发上限读取与修改接口"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.system_settings import (
    SystemRuntimeSettingsResponseSchema,
    SystemRuntimeSettingsUpdateSchema,
)
from app.services.system_settings_service import (
    get_system_runtime_settings,
    update_max_concurrent_workflows,
)

router = APIRouter(prefix="/api/system-settings", tags=["system-settings"])


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
