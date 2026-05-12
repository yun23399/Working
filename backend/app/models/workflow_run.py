"""工作流运行记录模型，负责保存断点快照与控制状态"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WorkflowRun(Base):
    """工作流运行记录模型，记录当前执行轮次、快照和控制指令"""

    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="running",
        server_default="running",
    )
    checkpoint_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
        server_default="{}",
    )
    control_signal: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="none",
        server_default="none",
    )
    redirect_instruction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
