"""用户自定义 Agent 角色模板路由，提供增删改查接口"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.agent_role_template import (
    AgentRoleTemplateCreateSchema,
    AgentRoleTemplateExportBundleSchema,
    AgentRoleTemplateImportRequestSchema,
    AgentRoleTemplateImportResponseSchema,
    AgentRoleTemplateResponseSchema,
    AgentRoleTemplateUpdateSchema,
)
from app.services.agent_role_template_service import (
    AgentRoleTemplateConflictError,
    AgentRoleTemplateNotFoundError,
    create_agent_role_template,
    delete_agent_role_template,
    export_agent_role_templates,
    import_agent_role_templates,
    list_agent_role_templates,
    template_model_to_response,
    update_agent_role_template,
)

router = APIRouter(prefix="/api/agent-role-templates", tags=["agent-role-templates"])


@router.get("", response_model=list[AgentRoleTemplateResponseSchema])
def get_agent_role_template_list_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentRoleTemplateResponseSchema]:
    """返回当前用户的全部自定义角色模板"""

    try:
        templates = list_agent_role_templates(db, current_user)
        return [template_model_to_response(item) for item in templates]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "获取自定义角色模板失败",
                "code": "LIST_AGENT_ROLE_TEMPLATES_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post("", response_model=AgentRoleTemplateResponseSchema)
def create_agent_role_template_endpoint(
    payload: AgentRoleTemplateCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRoleTemplateResponseSchema:
    """为当前用户创建自定义角色模板"""

    try:
        template = create_agent_role_template(db, current_user, payload)
        return template_model_to_response(template)
    except AgentRoleTemplateConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "自定义角色模板已存在",
                "code": "AGENT_ROLE_TEMPLATE_CONFLICT",
                "detail": f"角色 `{exc}` 已存在，请更换角色名称",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "创建自定义角色模板失败",
                "code": "CREATE_AGENT_ROLE_TEMPLATE_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.get("/export", response_model=AgentRoleTemplateExportBundleSchema)
def export_agent_role_template_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRoleTemplateExportBundleSchema:
    """导出当前用户的全部自定义角色模板"""

    try:
        return export_agent_role_templates(db, current_user)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "导出自定义角色模板失败",
                "code": "EXPORT_AGENT_ROLE_TEMPLATES_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.post("/import", response_model=AgentRoleTemplateImportResponseSchema)
def import_agent_role_template_endpoint(
    payload: AgentRoleTemplateImportRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRoleTemplateImportResponseSchema:
    """导入角色模板配置，并按冲突策略创建或覆盖现有模板"""

    try:
        return import_agent_role_templates(
            db,
            current_user,
            payload.bundle.templates,
            payload.conflict_strategy,
        )
    except AgentRoleTemplateConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "导入自定义角色模板失败",
                "code": "AGENT_ROLE_TEMPLATE_CONFLICT",
                "detail": f"角色 `{exc}` 已存在，请调整导入策略或角色名称",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "导入自定义角色模板失败",
                "code": "IMPORT_AGENT_ROLE_TEMPLATES_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.put("/{template_id}", response_model=AgentRoleTemplateResponseSchema)
def update_agent_role_template_endpoint(
    template_id: str,
    payload: AgentRoleTemplateUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRoleTemplateResponseSchema:
    """更新当前用户的指定自定义角色模板"""

    try:
        template = update_agent_role_template(db, current_user, template_id, payload)
        return template_model_to_response(template)
    except AgentRoleTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "自定义角色模板不存在",
                "code": "AGENT_ROLE_TEMPLATE_NOT_FOUND",
                "detail": f"角色模板 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except AgentRoleTemplateConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "自定义角色模板已存在",
                "code": "AGENT_ROLE_TEMPLATE_CONFLICT",
                "detail": f"角色 `{exc}` 已存在，请更换角色名称",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "更新自定义角色模板失败",
                "code": "UPDATE_AGENT_ROLE_TEMPLATE_FAILED",
                "detail": str(exc),
            },
        ) from exc


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_role_template_endpoint(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """删除当前用户的指定自定义角色模板"""

    try:
        delete_agent_role_template(db, current_user, template_id)
    except AgentRoleTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "自定义角色模板不存在",
                "code": "AGENT_ROLE_TEMPLATE_NOT_FOUND",
                "detail": f"角色模板 `{exc}` 不存在或无权访问",
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "删除自定义角色模板失败",
                "code": "DELETE_AGENT_ROLE_TEMPLATE_FAILED",
                "detail": str(exc),
            },
        ) from exc
