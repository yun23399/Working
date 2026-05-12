"""认证服务层，处理注册、登录与用户查询逻辑"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import LoginRequestSchema, RegisterRequestSchema
from app.utils.security import create_access_token, hash_password, verify_password


class UsernameAlreadyExistsError(Exception):
    """用户名已存在异常，供路由层转换为业务错误响应"""


class InvalidCredentialsError(Exception):
    """登录凭证无效异常，供路由层转换为业务错误响应"""


def register_user(db: Session, payload: RegisterRequestSchema) -> User:
    """创建新用户并写入数据库，若用户名重复则抛出异常"""

    existing_user = db.scalar(select(User).where(User.username == payload.username))
    if existing_user is not None:
        raise UsernameAlreadyExistsError(payload.username)

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, payload: LoginRequestSchema) -> tuple[str, User]:
    """校验登录请求，成功时返回访问令牌与用户对象"""

    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError(payload.username)

    access_token = create_access_token(str(user.id))
    return access_token, user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """根据主键查询用户对象，用于认证依赖加载当前用户"""

    return db.get(User, user_id)
