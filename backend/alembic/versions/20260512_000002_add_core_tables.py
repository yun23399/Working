"""创建阶段一核心数据表"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260512_000002"
down_revision = "20260512_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建用户、对话和消息核心表结构"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_users_id", "users", ["id"], unique=False)
        op.create_index("ix_users_username", "users", ["username"], unique=True)

    if not inspector.has_table("conversations"):
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
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
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )
        op.create_index("ix_conversations_id", "conversations", ["id"], unique=False)
        op.create_index(
            "ix_conversations_user_id", "conversations", ["user_id"], unique=False
        )

    if not inspector.has_table("messages"):
        op.create_table(
            "messages",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("conversation_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=30), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        )
        op.create_index("ix_messages_id", "messages", ["id"], unique=False)
        op.create_index(
            "ix_messages_conversation_id", "messages", ["conversation_id"], unique=False
        )


def downgrade() -> None:
    """删除阶段一核心表结构"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("messages"):
        op.drop_index("ix_messages_conversation_id", table_name="messages")
        op.drop_index("ix_messages_id", table_name="messages")
        op.drop_table("messages")

    if inspector.has_table("conversations"):
        op.drop_index("ix_conversations_user_id", table_name="conversations")
        op.drop_index("ix_conversations_id", table_name="conversations")
        op.drop_table("conversations")

    if inspector.has_table("users"):
        op.drop_index("ix_users_username", table_name="users")
        op.drop_index("ix_users_id", table_name="users")
        op.drop_table("users")
