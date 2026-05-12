"""预置角色模板定义，供工作流规划与执行阶段复用"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleTemplate:
    """角色模板对象，描述预设职责、提示词和默认工具"""

    template_id: str
    role_name: str
    summary: str
    system_prompt: str
    default_tools: list[str]
    max_retries: int


ROLE_TEMPLATES: dict[str, RoleTemplate] = {
    "pm": RoleTemplate(
        template_id="pm",
        role_name="PM",
        summary="负责梳理需求目标、范围边界、优先级与交付节奏。",
        system_prompt=(
            "你是项目管理角色，负责将需求整理成可执行的阶段目标、"
            "范围边界、约束和交付计划。输出必须简洁、结构清晰、便于后续角色接手。"
        ),
        default_tools=["file_tool"],
        max_retries=2,
    ),
    "frontend": RoleTemplate(
        template_id="frontend",
        role_name="前端工程师",
        summary="负责页面结构、交互细节、组件拆分与前端交付草稿。",
        system_prompt=(
            "你是前端工程师，重点关注界面结构、组件拆分、交互流程、"
            "状态变化和用户体验。输出要强调页面实现与交互要点。"
        ),
        default_tools=["file_tool", "browser_tool", "code_executor"],
        max_retries=3,
    ),
    "backend": RoleTemplate(
        template_id="backend",
        role_name="后端工程师",
        summary="负责接口、数据结构、执行逻辑和服务端实现方案。",
        system_prompt=(
            "你是后端工程师，重点关注接口契约、数据结构、服务边界、"
            "错误处理和执行流程。输出要体现可落地的服务端实现思路。"
        ),
        default_tools=["file_tool", "api_caller", "code_executor"],
        max_retries=3,
    ),
    "qa": RoleTemplate(
        template_id="qa",
        role_name="测试工程师",
        summary="负责校验链路、风险点、回归策略与验收项。",
        system_prompt=(
            "你是测试工程师，重点关注风险识别、验收条件、回归范围、"
            "失败场景和验证步骤。输出要便于直接执行测试。"
        ),
        default_tools=["file_tool", "browser_tool"],
        max_retries=2,
    ),
    "designer": RoleTemplate(
        template_id="designer",
        role_name="设计师",
        summary="负责视觉方向、布局层级、组件表达与设计说明。",
        system_prompt=(
            "你是设计师，重点关注视觉表达、信息层级、版式结构、"
            "设计一致性和交互感受。输出要体现界面与体验方向。"
        ),
        default_tools=["file_tool"],
        max_retries=2,
    ),
}


def get_role_template(template_id: str) -> RoleTemplate:
    """根据模板编号读取预置角色模板，不存在时抛出明确错误"""

    template = ROLE_TEMPLATES.get(template_id)
    if template is None:
        raise KeyError(f"未知角色模板：{template_id}")
    return template


def list_role_templates() -> list[RoleTemplate]:
    """返回全部预置角色模板，供规划器选择候选角色"""

    return list(ROLE_TEMPLATES.values())
