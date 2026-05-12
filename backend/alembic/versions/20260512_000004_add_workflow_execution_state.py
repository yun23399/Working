"""为工作流表补充执行状态与日志字段"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260512_000004"
down_revision = "20260512_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """新增工作流执行进度与执行日志字段"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("workflows")}

    if "execution_log_json" not in columns:
        op.add_column(
            "workflows",
            sa.Column(
                "execution_log_json",
                sa.Text(),
                nullable=False,
                server_default="[]",
            ),
        )

    if "progress" not in columns:
        op.add_column(
            "workflows",
            sa.Column(
                "progress",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade() -> None:
    """移除工作流执行进度与执行日志字段"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("workflows")}

    if "progress" in columns:
        op.drop_column("workflows", "progress")

    if "execution_log_json" in columns:
        op.drop_column("workflows", "execution_log_json")
