"""新增工作流运行记录表"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260513_000006"
down_revision = "20260513_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建工作流运行记录表，用于断点与控制指令持久化"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if "workflow_runs" in table_names:
        return

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="running",
        ),
        sa.Column("checkpoint_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "control_signal",
            sa.String(length=30),
            nullable=False,
            server_default="none",
        ),
        sa.Column(
            "redirect_instruction",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_runs_id", "workflow_runs", ["id"])
    op.create_index("ix_workflow_runs_workflow_id", "workflow_runs", ["workflow_id"])


def downgrade() -> None:
    """移除工作流运行记录表"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if "workflow_runs" not in table_names:
        return

    op.drop_index("ix_workflow_runs_workflow_id", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_id", table_name="workflow_runs")
    op.drop_table("workflow_runs")
