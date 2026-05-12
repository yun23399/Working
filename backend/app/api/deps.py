"""API 公共依赖模块，提供数据库会话与当前用户解析能力"""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import get_user_by_id
from app.utils.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """提供请求级数据库会话，并在请求结束后自动关闭连接"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """解析 Bearer Token 并加载当前用户，失败时抛出 401"""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "缺少访问令牌",
                "code": "MISSING_TOKEN",
                "detail": "请在 Authorization 头中提供 Bearer Token",
            },
        )

    try:
        user_id = int(decode_access_token(credentials.credentials))
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "访问令牌无效",
                "code": "INVALID_TOKEN",
                "detail": str(exc),
            },
        ) from exc

    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "用户不存在",
                "code": "USER_NOT_FOUND",
                "detail": "访问令牌对应的用户已不存在",
            },
        )

    return user
