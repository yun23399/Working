"""为对话补充总代理角色字段"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260513_000008"
down_revision = "20260513_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """为 conversations 表新增 manager_role 字段"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("conversations")}
    if "manager_role" in columns:
        return

    op.add_column(
        "conversations",
        sa.Column(
            "manager_role",
            sa.String(length=50),
            nullable=False,
            server_default="general_manager",
        ),
    )


def downgrade() -> None:
    """移除 conversations 表中的 manager_role 字段"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("conversations")}
    if "manager_role" not in columns:
        return

    op.drop_column("conversations", "manager_role")
