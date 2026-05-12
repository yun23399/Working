"""${message}"""

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """执行升级迁移"""


def downgrade() -> None:
    """执行降级迁移"""
