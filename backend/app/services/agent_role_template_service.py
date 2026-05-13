"""用户自定义 Agent 角色模板服务层，负责 CRUD 与工作流模板解析"""

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.templates.role_templates import RoleTemplate
from app.models.agent_role_template import AgentRoleTemplate
from app.models.user import User
from app.schemas.agent_role_template import (
    AgentRoleTemplateCreateSchema,
    AgentRoleTemplateResponseSchema,
    AgentRoleTemplateUpdateSchema,
)

SUPPORTED_TEMPLATE_TOOLS = {
    "file_tool",
    "api_caller",
    "browser_tool",
    "image_tool",
    "code_executor",
}


class AgentRoleTemplateNotFoundError(Exception):
    """自定义角色模板不存在异常"""


class AgentRoleTemplateConflictError(Exception):
    """自定义角色模板冲突异常"""


@dataclass(frozen=True)
class CustomRoleTemplate:
    """运行时自定义角色模板对象，供工作流规划与执行阶段复用"""

    template_id: str
    role_name: str
    summary: str
    system_prompt: str
    default_tools: list[str]
    max_retries: int
    trigger_keywords: list[str]
    is_enabled: bool
    source: str = "custom"

    def to_role_template(self) -> RoleTemplate:
        """转换为执行阶段可消费的最小角色模板结构"""

        return RoleTemplate(
            template_id=self.template_id,
            role_name=self.role_name,
            summary=self.summary,
            system_prompt=self.system_prompt,
            default_tools=self.default_tools,
            max_retries=self.max_retries,
            source=self.source,
            trigger_keywords=self.trigger_keywords,
            is_enabled=self.is_enabled,
        )


def normalize_text(value: str) -> str:
    """清洗输入文本，避免多余空白进入模板定义"""

    return " ".join(value.strip().split())


def normalize_multiline_text(value: str) -> str:
    """清洗多行文本，保留换行语义并去除空白行尾部空格"""

    return "\n".join(
        line.rstrip() for line in value.strip().splitlines() if line.strip()
    )


def normalize_keywords(keywords: list[str]) -> list[str]:
    """规范化触发关键词列表，并去除空值与重复项"""

    deduplicated: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        normalized_keyword = normalize_text(keyword).lower()
        if not normalized_keyword or normalized_keyword in seen:
            continue
        seen.add(normalized_keyword)
        deduplicated.append(normalized_keyword)

    return deduplicated


def normalize_tools(tools: list[str]) -> list[str]:
    """过滤自定义角色可用工具，只保留当前受支持的工具集合"""

    normalized_tools: list[str] = []
    seen: set[str] = set()
    for tool in tools:
        normalized_tool = normalize_text(tool)
        if not normalized_tool or normalized_tool not in SUPPORTED_TEMPLATE_TOOLS:
            continue
        if normalized_tool in seen:
            continue
        seen.add(normalized_tool)
        normalized_tools.append(normalized_tool)

    return normalized_tools


def build_template_id(user: User, role_name: str, existing_ids: set[str]) -> str:
    """为用户自定义角色生成稳定模板编号，避免与现有模板冲突"""

    slug = "".join(
        char.lower() if char.isalnum() else "-" for char in normalize_text(role_name)
    ).strip("-")
    slug = slug or "custom-role"
    base_template_id = f"user-{user.id}-{slug}"
    next_template_id = base_template_id
    suffix = 1

    while next_template_id in existing_ids:
        suffix += 1
        next_template_id = f"{base_template_id}-{suffix}"

    return next_template_id


def template_model_to_runtime(model: AgentRoleTemplate) -> CustomRoleTemplate:
    """将数据库模型转换为运行时自定义模板对象"""

    return CustomRoleTemplate(
        template_id=model.template_id,
        role_name=model.role_name,
        summary=model.summary,
        system_prompt=model.system_prompt,
        default_tools=json.loads(model.default_tools_json),
        max_retries=model.max_retries,
        trigger_keywords=json.loads(model.trigger_keywords_json),
        is_enabled=model.is_enabled,
    )


def template_model_to_response(
    model: AgentRoleTemplate,
) -> AgentRoleTemplateResponseSchema:
    """将数据库模型转换为接口响应结构"""

    return AgentRoleTemplateResponseSchema(
        template_id=model.template_id,
        role_name=model.role_name,
        summary=model.summary,
        system_prompt=model.system_prompt,
        trigger_keywords=json.loads(model.trigger_keywords_json),
        default_tools=json.loads(model.default_tools_json),
        max_retries=model.max_retries,
        is_enabled=model.is_enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def list_agent_role_templates(
    db: Session,
    user: User,
) -> list[AgentRoleTemplate]:
    """返回当前用户的全部自定义角色模板"""

    statement = (
        select(AgentRoleTemplate)
        .where(AgentRoleTemplate.user_id == user.id)
        .order_by(AgentRoleTemplate.updated_at.desc(), AgentRoleTemplate.id.desc())
    )
    return list(db.scalars(statement).all())


def list_enabled_custom_role_templates(
    db: Session,
    user: User,
) -> list[CustomRoleTemplate]:
    """返回当前用户启用中的自定义角色模板，供工作流规划阶段匹配"""

    statement = (
        select(AgentRoleTemplate)
        .where(
            AgentRoleTemplate.user_id == user.id,
            AgentRoleTemplate.is_enabled.is_(True),
        )
        .order_by(AgentRoleTemplate.updated_at.desc(), AgentRoleTemplate.id.desc())
    )
    return [template_model_to_runtime(item) for item in db.scalars(statement).all()]


def get_agent_role_template_by_template_id(
    db: Session,
    user: User,
    template_id: str,
) -> AgentRoleTemplate:
    """按模板编号读取当前用户的自定义角色模板"""

    statement = select(AgentRoleTemplate).where(
        AgentRoleTemplate.user_id == user.id,
        AgentRoleTemplate.template_id == template_id,
    )
    template = db.scalar(statement)
    if template is None:
        raise AgentRoleTemplateNotFoundError(template_id)
    return template


def create_agent_role_template(
    db: Session,
    user: User,
    payload: AgentRoleTemplateCreateSchema,
) -> AgentRoleTemplate:
    """创建当前用户的自定义角色模板"""

    normalized_role_name = normalize_text(payload.role_name)
    existing_templates = list_agent_role_templates(db, user)
    if any(item.role_name == normalized_role_name for item in existing_templates):
        raise AgentRoleTemplateConflictError(normalized_role_name)

    template = AgentRoleTemplate(
        user_id=user.id,
        template_id=build_template_id(
            user,
            normalized_role_name,
            {item.template_id for item in existing_templates},
        ),
        role_name=normalized_role_name,
        summary=normalize_text(payload.summary),
        system_prompt=normalize_multiline_text(payload.system_prompt),
        trigger_keywords_json=json.dumps(
            normalize_keywords(payload.trigger_keywords),
            ensure_ascii=False,
        ),
        default_tools_json=json.dumps(
            normalize_tools(payload.default_tools) or ["file_tool"],
            ensure_ascii=False,
        ),
        max_retries=payload.max_retries,
        is_enabled=payload.is_enabled,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_agent_role_template(
    db: Session,
    user: User,
    template_id: str,
    payload: AgentRoleTemplateUpdateSchema,
) -> AgentRoleTemplate:
    """更新当前用户的自定义角色模板"""

    template = get_agent_role_template_by_template_id(db, user, template_id)
    normalized_role_name = normalize_text(payload.role_name)
    existing_templates = list_agent_role_templates(db, user)
    if any(
        item.template_id != template_id and item.role_name == normalized_role_name
        for item in existing_templates
    ):
        raise AgentRoleTemplateConflictError(normalized_role_name)

    template.role_name = normalized_role_name
    template.summary = normalize_text(payload.summary)
    template.system_prompt = normalize_multiline_text(payload.system_prompt)
    template.trigger_keywords_json = json.dumps(
        normalize_keywords(payload.trigger_keywords),
        ensure_ascii=False,
    )
    template.default_tools_json = json.dumps(
        normalize_tools(payload.default_tools) or ["file_tool"],
        ensure_ascii=False,
    )
    template.max_retries = payload.max_retries
    template.is_enabled = payload.is_enabled
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def delete_agent_role_template(
    db: Session,
    user: User,
    template_id: str,
) -> None:
    """删除当前用户的自定义角色模板"""

    template = get_agent_role_template_by_template_id(db, user, template_id)
    db.delete(template)
    db.commit()


def resolve_custom_role_template(
    db: Session,
    template_id: str,
) -> RoleTemplate:
    """按模板编号解析自定义角色模板，供执行阶段读取模板快照失败时兜底"""

    statement = select(AgentRoleTemplate).where(
        AgentRoleTemplate.template_id == template_id
    )
    template = db.scalar(statement)
    if template is None:
        raise AgentRoleTemplateNotFoundError(template_id)
    return template_model_to_runtime(template).to_role_template()
