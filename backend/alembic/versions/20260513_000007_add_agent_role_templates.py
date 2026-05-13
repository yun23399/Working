"""新增用户自定义 Agent 角色模板表"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260513_000007"
down_revision = "20260513_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建用户自定义角色模板表，用于设置页管理与工作流规划复用"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if "agent_role_templates" in table_names:
        return

    op.create_table(
        "agent_role_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.String(length=80), nullable=False),
        sa.Column("role_name", sa.String(length=80), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("trigger_keywords_json", sa.Text(), nullable=False),
        sa.Column("default_tools_json", sa.Text(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id"),
    )
    op.create_index(
        "ix_agent_role_templates_id",
        "agent_role_templates",
        ["id"],
    )
    op.create_index(
        "ix_agent_role_templates_user_id",
        "agent_role_templates",
        ["user_id"],
    )


def downgrade() -> None:
    """移除用户自定义角色模板表"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if "agent_role_templates" not in table_names:
        return

    op.drop_index("ix_agent_role_templates_user_id", table_name="agent_role_templates")
    op.drop_index("ix_agent_role_templates_id", table_name="agent_role_templates")
    op.drop_table("agent_role_templates")
