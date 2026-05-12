"""为工作流表补充共享工作区状态字段"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260513_000005"
down_revision = "20260512_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """新增工作区路径、状态快照和交接记录字段"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("workflows")}

    if "workspace_state_json" not in columns:
        op.add_column(
            "workflows",
            sa.Column(
                "workspace_state_json",
                sa.Text(),
                nullable=False,
                server_default="{}",
            ),
        )

    if "handoff_log_json" not in columns:
        op.add_column(
            "workflows",
            sa.Column(
                "handoff_log_json",
                sa.Text(),
                nullable=False,
                server_default="[]",
            ),
        )

    if "workspace_path" not in columns:
        op.add_column(
            "workflows",
            sa.Column(
                "workspace_path",
                sa.String(length=255),
                nullable=False,
                server_default="",
            ),
        )


def downgrade() -> None:
    """移除共享工作区相关字段"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("workflows")}

    if "workspace_path" in columns:
        op.drop_column("workflows", "workspace_path")

    if "handoff_log_json" in columns:
        op.drop_column("workflows", "handoff_log_json")

    if "workspace_state_json" in columns:
        op.drop_column("workflows", "workspace_state_json")
