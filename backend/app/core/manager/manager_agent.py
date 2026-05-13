"""Manager Agent 实现，负责需求收集、进度判断与对话回复"""

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from loguru import logger

from app.config import settings
from app.core.llm.adapter import ChatMessage, LLMAdapter

MANAGER_ROLE_LABELS = {
    "general_manager": "总代理",
    "delivery_manager": "交付总代理",
    "product_manager": "产品总代理",
    "technical_manager": "技术总代理",
}


@dataclass(frozen=True)
class ManagerConversationMessage:
    """Manager Agent 使用的历史消息结构"""

    role: str
    content: str


@dataclass(frozen=True)
class ManagerProgressState:
    """总代理需求收集进度结构，供前后端共同消费"""

    selected_role: str
    completion_score: int
    readiness_threshold: int
    is_ready_to_start: bool
    missing_slots: list[str]
    collected_points: list[str]
    suggested_next_questions: list[str]
    summary: str


class ManagerAgent:
    """Manager Agent，负责需求澄清、准备度判断与启动前对话"""

    def __init__(self, adapter: LLMAdapter | None = None) -> None:
        """初始化 Manager Agent，并注入统一的 LLM 适配器"""

        self.adapter = adapter or LLMAdapter()

    def get_runtime_label(self) -> str:
        """返回当前运行时模型标识，供日志与前端提示展示"""

        return self.adapter.get_runtime_label()

    def resolve_role_label(self, manager_role: str) -> str:
        """将内部总代理角色编号转换为界面与提示词可读名称"""

        return MANAGER_ROLE_LABELS.get(manager_role, "总代理")

    def extract_user_messages(
        self, history_messages: Sequence[ManagerConversationMessage]
    ) -> list[str]:
        """提取历史中的用户消息，作为需求收集分析输入"""

        return [
            message.content.strip()
            for message in history_messages
            if message.role == "user" and message.content.strip()
        ]

    def analyze_progress(
        self,
        manager_role: str,
        conversation_title: str | None,
        history_messages: Sequence[ManagerConversationMessage],
    ) -> ManagerProgressState:
        """基于当前对话历史评估总代理是否已足够理解需求"""

        user_messages = self.extract_user_messages(history_messages)
        combined_text = "\n".join(user_messages)
        normalized_text = combined_text.lower()

        goal_keywords = (
            "要做",
            "需要",
            "目标",
            "需求",
            "项目",
            "交付",
            "完成",
            "实现",
            "功能",
            "task",
            "goal",
        )
        scope_keywords = (
            "页面",
            "界面",
            "接口",
            "文档",
            "流程",
            "模块",
            "范围",
            "包括",
            "前端",
            "后端",
            "聊天页",
            "设置页",
            "frontend",
            "backend",
        )
        constraint_keywords = (
            "必须",
            "限制",
            "优先",
            "风格",
            "端口",
            "模型",
            "api",
            "数据库",
            "不能",
        )
        acceptance_keywords = (
            "验收",
            "完成",
            "效果",
            "上线",
            "开始任务",
            "交付",
            "github",
            "push",
        )

        missing_slots: list[str] = []
        collected_points: list[str] = []
        score = 10

        if conversation_title and conversation_title.strip():
            score += 10
            collected_points.append(f"已形成对话标题：{conversation_title.strip()}")
        else:
            missing_slots.append("项目标题或任务主题")

        if any(keyword in normalized_text for keyword in goal_keywords):
            score += 25
            collected_points.append("已识别核心目标")
        else:
            missing_slots.append("核心目标")

        if any(keyword in normalized_text for keyword in scope_keywords):
            score += 20
            collected_points.append("已识别主要交付范围")
        else:
            missing_slots.append("交付范围")

        if any(keyword in normalized_text for keyword in constraint_keywords):
            score += 20
            collected_points.append("已识别关键约束与偏好")
        else:
            missing_slots.append("关键约束或偏好")

        if any(keyword in normalized_text for keyword in acceptance_keywords):
            score += 15
            collected_points.append("已识别开始条件或验收预期")
        else:
            missing_slots.append("验收标准或开始条件")

        if len(user_messages) >= 3:
            score += 10
            collected_points.append("用户已进行了多轮补充说明")
        else:
            missing_slots.append("多轮补充说明")

        completion_score = min(score, 100)
        readiness_threshold = settings.manager_readiness_threshold
        is_ready_to_start = (
            completion_score >= readiness_threshold and len(missing_slots) <= 2
        )

        if not collected_points:
            collected_points.append("当前还没有收集到足够的任务线索")

        suggested_next_questions = self.build_next_questions(missing_slots)
        manager_label = self.resolve_role_label(manager_role)
        summary = (
            f"{manager_label} 当前已掌握 {completion_score}% 的任务信息。"
            if is_ready_to_start
            else f"{manager_label} 仍在补齐关键信息，当前完成度约 {completion_score}%。"
        )

        return ManagerProgressState(
            selected_role=manager_role,
            completion_score=completion_score,
            readiness_threshold=readiness_threshold,
            is_ready_to_start=is_ready_to_start,
            missing_slots=missing_slots,
            collected_points=collected_points,
            suggested_next_questions=suggested_next_questions,
            summary=summary,
        )

    def build_next_questions(self, missing_slots: list[str]) -> list[str]:
        """根据当前缺口生成下一轮优先追问项"""

        question_map = {
            "项目标题或任务主题": "这次任务希望以什么项目名或主题推进？",
            "核心目标": "你最希望这次任务最终完成什么结果？",
            "交付范围": "这次要覆盖哪些页面、接口、流程或文档？",
            "关键约束或偏好": "有没有必须使用的技术、接口、风格、端口或外部服务？",
            "验收标准或开始条件": "你认为什么状态可以算任务准备完成并开始执行？",
            "多轮补充说明": "还有哪些背景、已有素材或历史约束需要总代理一并考虑？",
        }
        return [
            question_map[slot] for slot in missing_slots[:3] if slot in question_map
        ]

    def build_system_prompt(
        self,
        manager_role: str,
        conversation_title: str | None,
        progress_state: ManagerProgressState,
    ) -> str:
        """构造总代理系统提示词，约束回答风格与阶段职责"""

        title_segment = (
            f"当前对话标题是《{conversation_title}》。"
            if conversation_title
            else "当前对话还没有明确项目标题。"
        )
        manager_label = self.resolve_role_label(manager_role)
        readiness_segment = (
            f"当前需求收集完成度约为 {progress_state.completion_score}% ，"
            f"开始阈值为 {progress_state.readiness_threshold}% 。"
        )
        missing_segment = (
            "当前仍缺少的信息包括："
            + "、".join(progress_state.missing_slots[:4])
            + "。"
            if progress_state.missing_slots
            else "当前关键信息已经基本齐备。"
        )
        start_guideline = (
            "如果你判断已经足够理解需求，请在回复中明确告诉用户“可以开始任务了”，"
            "并概括将由你拆分和指派的执行方向。"
            if progress_state.is_ready_to_start
            else "当前不要直接进入任务执行规划，优先通过简洁追问补齐缺口。"
        )
        return (
            f"你是多智能体编排平台中的{manager_label}。"
            "你的职责不是直接执行任务，而是持续和用户沟通，补齐任务目标、范围、约束、验收与偏好。"
            "你需要像真正的项目总代理一样，主动提出可选项、指出信息缺口，并在理解足够完整后明确告知用户可以开始任务。"
            "回复语言默认与用户保持一致，优先使用中文。"
            "每次回复尽量包含：1）你已理解到的内容；2）仍缺失的关键点；3）下一步建议或问题。"
            f"{title_segment}{readiness_segment}{missing_segment}{start_guideline}"
        )

    def normalize_role(self, role: str) -> str:
        """标准化历史消息角色，避免无效角色传入模型上下文"""

        return role if role in {"system", "user", "assistant"} else "user"

    def build_messages(
        self,
        manager_role: str,
        conversation_title: str | None,
        history_messages: Sequence[ManagerConversationMessage],
    ) -> list[ChatMessage]:
        """组合系统提示词与历史消息，生成发送给 LLM 的上下文"""

        progress_state = self.analyze_progress(
            manager_role, conversation_title, history_messages
        )
        messages: list[ChatMessage] = [
            ChatMessage(
                role="system",
                content=self.build_system_prompt(
                    manager_role,
                    conversation_title,
                    progress_state,
                ),
            )
        ]
        for message in history_messages:
            messages.append(
                ChatMessage(
                    role=self.normalize_role(message.role),
                    content=message.content,
                )
            )
        return messages

    async def stream_reply(
        self,
        manager_role: str,
        conversation_title: str | None,
        history_messages: Sequence[ManagerConversationMessage],
    ) -> AsyncIterator[str]:
        """基于历史消息生成总代理的真实流式回复"""

        try:
            messages = self.build_messages(
                manager_role,
                conversation_title,
                history_messages,
            )
            async for token in self.adapter.stream_chat(messages):
                yield token
        except Exception as exc:
            logger.exception("Manager 流式回复生成失败: {}", exc)
            raise
