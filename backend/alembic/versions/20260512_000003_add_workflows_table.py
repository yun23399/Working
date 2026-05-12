"""创建阶段二工作流预览表"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260512_000003"
down_revision = "20260512_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建工作流预览表结构"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("workflows"):
        return

    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("requirement_json", sa.Text(), nullable=False),
        sa.Column("dag_json", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
    )
    op.create_index("ix_workflows_id", "workflows", ["id"], unique=False)
    op.create_index(
        "ix_workflows_conversation_id",
        "workflows",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    """删除工作流预览表结构"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("workflows"):
        return

    op.drop_index("ix_workflows_conversation_id", table_name="workflows")
    op.drop_index("ix_workflows_id", table_name="workflows")
    op.drop_table("workflows")
