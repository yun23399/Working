"""需求提取器，负责将对话历史整理为结构化需求摘要"""

from dataclasses import dataclass

from app.core.manager.manager_agent import ManagerConversationMessage


@dataclass(frozen=True)
class RequirementSummary:
    """结构化需求对象，供工作流规划器消费"""

    goal: str
    constraints: list[str]
    output_types: list[str]
    context: str


class RequirementExtractor:
    """需求提取器，基于历史消息归纳任务目标与约束"""

    def extract(
        self,
        conversation_title: str | None,
        history_messages: list[ManagerConversationMessage],
    ) -> RequirementSummary:
        """从对话历史生成最小结构化需求摘要"""

        user_messages = [
            message.content.strip()
            for message in history_messages
            if message.role == "user" and message.content.strip()
        ]
        assistant_messages = [
            message.content.strip()
            for message in history_messages
            if message.role == "assistant" and message.content.strip()
        ]

        latest_user_message = (
            user_messages[-1]
            if user_messages
            else conversation_title or "用户尚未提供明确需求"
        )
        goal = latest_user_message[:240]

        constraints: list[str] = []
        if conversation_title:
            constraints.append(f"需围绕当前对话《{conversation_title}》推进")
        if len(user_messages) > 1:
            constraints.append("需要综合本轮之前的多条用户补充说明")
        if any("文档" in message for message in user_messages):
            constraints.append("交付内容需兼顾文档表达清晰度")
        if any("页面" in message or "前端" in message for message in user_messages):
            constraints.append("需要体现前端界面或交互实现要求")
        if not constraints:
            constraints.append("需求仍处于阶段二预览模式，待用户确认后再执行")

        output_types = self.infer_output_types(user_messages)
        context_segments = user_messages[-3:]
        if assistant_messages:
            latest_summary = assistant_messages[-1][:160]
            context_segments.append(f"最近一次 Manager 总结：{latest_summary}")

        return RequirementSummary(
            goal=goal,
            constraints=constraints,
            output_types=output_types,
            context="\n".join(context_segments)[:1200],
        )

    def infer_output_types(self, user_messages: list[str]) -> list[str]:
        """根据用户消息推断可能的交付物类型列表"""

        combined_text = "\n".join(user_messages)
        output_types: list[str] = []
        if any(
            keyword in combined_text for keyword in ("页面", "前端", "界面", "网页")
        ):
            output_types.append("code")
        if any(
            keyword in combined_text for keyword in ("文档", "说明", "流程", "方案")
        ):
            output_types.append("document")
        if any(keyword in combined_text for keyword in ("图片", "图", "设计")):
            output_types.append("image")
        if not output_types:
            output_types.append("document")
        return output_types
