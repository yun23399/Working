"""角色模板模块导出"""

from app.agents.templates.role_templates import (
    ROLE_TEMPLATES,
    RoleTemplate,
    get_role_template,
    list_role_templates,
)

__all__ = [
    "ROLE_TEMPLATES",
    "RoleTemplate",
    "get_role_template",
    "list_role_templates",
]
