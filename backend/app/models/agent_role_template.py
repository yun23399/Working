"""用户自定义 Agent 角色模板模型，负责持久化角色配置"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentRoleTemplate(Base):
    """用户级自定义角色模板，描述角色职责、提示词与触发关键词"""

    __tablename__ = "agent_role_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    role_name: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_keywords_json: Mapped[str] = mapped_column(Text, nullable=False)
    default_tools_json: Mapped[str] = mapped_column(Text, nullable=False)
    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="2",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
