"""插件管理路由，提供本地插件列表读取与启停控制接口"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.plugin import PluginSettingsResponseSchema, PluginSettingsUpdateSchema
from app.services.plugin_service import (
    PluginNotFoundError,
    list_plugin_settings,
    update_plugin_enabled_state,
)

router = APIRouter(prefix="/api/system-settings/plugins", tags=["plugins"])


@router.get("", response_model=list[PluginSettingsResponseSchema])
def list_plugins_endpoint(
    _: User = Depends(get_current_user),
) -> list[PluginSettingsResponseSchema]:
    """返回当前仓库已安装插件列表，供设置页展示"""

    try:
        return list_plugin_settings()
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "读取插件列表失败",
                "code": "LIST_PLUGINS_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.put("/{plugin_id}", response_model=PluginSettingsResponseSchema)
def update_plugin_enabled_state_endpoint(
    plugin_id: str,
    payload: PluginSettingsUpdateSchema,
    _: User = Depends(get_current_user),
) -> PluginSettingsResponseSchema:
    """更新指定插件的启停状态，并写回仓库根目录 `.env`"""

    try:
        return update_plugin_enabled_state(plugin_id, payload.is_enabled)
    except PluginNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "插件不存在",
                "code": "PLUGIN_NOT_FOUND",
                "detail": str(exc),
            },
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "更新插件状态失败",
                "code": "UPDATE_PLUGIN_STATE_FAILED",
                "detail": str(exc),
            },
        ) from exc
