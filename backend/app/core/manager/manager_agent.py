"""Manager Agent 基础对话实现，负责组织上下文并调用 LLM"""

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from loguru import logger

from app.core.llm.adapter import ChatMessage, LLMAdapter


@dataclass(frozen=True)
class ManagerConversationMessage:
    """Manager Agent 使用的历史消息结构"""

    role: str
    content: str


class ManagerAgent:
    """Manager Agent，负责当前阶段的普通需求收集与对话回复"""

    def __init__(self, adapter: LLMAdapter | None = None) -> None:
        """初始化 Manager Agent，并注入统一的 LLM 适配器"""

        self.adapter = adapter or LLMAdapter()

    def get_runtime_label(self) -> str:
        """返回当前运行时模型标识，供日志与前端提示展示"""

        return self.adapter.get_runtime_label()

    def build_system_prompt(self, conversation_title: str | None) -> str:
        """构造 Manager 的系统提示词，约束回答风格与阶段职责"""

        title_segment = (
            f"当前对话标题是《{conversation_title}》。"
            if conversation_title
            else "当前对话还没有明确项目标题。"
        )
        return (
            "你是多智能体编排平台中的 Manager Agent。"
            "当前阶段只执行普通对话与需求澄清，不进入工作流规划。"
            "你的目标是准确理解用户需求，给出简洁、可执行的下一步建议。"
            "如果信息不足，优先提出关键澄清问题；如果需求已经明确，先总结目标与交付方向。"
            "回答语言默认与用户保持一致，优先使用中文。"
            f"{title_segment}"
        )

    def normalize_role(self, role: str) -> str:
        """标准化历史消息角色，避免无效角色传入模型上下文"""

        return role if role in {"system", "user", "assistant"} else "user"

    def build_messages(
        self,
        conversation_title: str | None,
        history_messages: Sequence[ManagerConversationMessage],
    ) -> list[ChatMessage]:
        """组合系统提示词与历史消息，生成发送给 LLM 的上下文"""

        messages: list[ChatMessage] = [
            ChatMessage(
                role="system",
                content=self.build_system_prompt(conversation_title),
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
        conversation_title: str | None,
        history_messages: Sequence[ManagerConversationMessage],
    ) -> AsyncIterator[str]:
        """基于历史消息生成 Manager 的真实流式回复"""

        try:
            messages = self.build_messages(conversation_title, history_messages)
            async for token in self.adapter.stream_chat(messages):
                yield token
        except Exception as exc:
            logger.exception("Manager 流式回复生成失败: {}", exc)
            raise
